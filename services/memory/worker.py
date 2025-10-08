
import os, json, asyncio, time, logging
from pathlib import Path
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError, UnknownTopicOrPartitionError
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import suppress
import httpx
from logging.handlers import RotatingFileHandler

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("MEMORY_COLLECTION", "chat_memory")
EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3")
EMBED_DIM = int(os.getenv("EMBED_DIM", "1024"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LOG_PATH = os.getenv("MEMORY_LOG_PATH", os.getenv("LOG_PATH", "/var/log/app/memory.log"))
TOPIC_IN_A = os.getenv("TOPIC_IN_A", "user_messages")
TOPIC_IN_B = os.getenv("TOPIC_IN_B", "model_responses")
TOPIC_OUT = os.getenv("TOPIC_OUT", "memory_events")
TOPICS = [TOPIC_IN_A, TOPIC_IN_B, TOPIC_OUT]
worker_task = None

logger = logging.getLogger("memory-worker")
logger.setLevel(logging.INFO)
if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)
    if LOG_PATH:
        try:
            Path(LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as exc:
            logger.warning("Failed to initialize file logger at %s: %s", LOG_PATH, exc)

topics_ready = False
async def ensure_topics():
    global topics_ready
    admin = AIOKafkaAdminClient(bootstrap_servers=BOOTSTRAP)
    try:
        existing = await admin.list_topics()
        missing = [name for name in TOPICS if name not in existing]
        if missing:
            logger.info("Creating missing topics: %s", ", ".join(missing))
            topics = [NewTopic(name=topic, num_partitions=1, replication_factor=1) for topic in missing]
            try:
                await admin.create_topics(new_topics=topics)
            except TopicAlreadyExistsError:
                logger.info("Topics already exist, continuing")
        topics_ready = True
    except Exception as exc:
        topics_ready = False
        logger.error("Topic verification failed: %s", exc)
    finally:
        await admin.close()

async def get_embedding(text: str) -> list[float]:
    payload = {"model": EMBED_MODEL, "prompt": text}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{OLLAMA_URL}/api/embeddings", json=payload)
        resp.raise_for_status()
        data = resp.json()
        vector = data.get("embedding") or []
        if not vector:
            raise ValueError("Empty embedding returned")
        if len(vector) != EMBED_DIM:
            raise ValueError(f"Expected embedding of size {EMBED_DIM}, got {len(vector)}")
        return vector

async def main_loop():
    client = QdrantClient(url=QDRANT_URL)
    try:
        client.get_collection(COLLECTION)
    except Exception as exc:
        logger.warning("Collection '%s' missing, recreating (%s)", COLLECTION, exc)
        client.recreate_collection(COLLECTION, vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE))

    consumer = AIOKafkaConsumer(TOPIC_IN_A, TOPIC_IN_B, bootstrap_servers=BOOTSTRAP, group_id="memory")
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    await consumer.start(); await producer.start()
    logger.info("Memory worker started")
    try:
        async for msg in consumer:
            try:
                data = json.loads(msg.value.decode())
            except Exception:
                continue
            text = data.get("text","")
            session_id = data.get("session_id","default")
            try:
                vec = await get_embedding(text)
            except Exception as exc:
                logger.error("Embedding failed for session %s: %s", session_id, exc)
                err_evt = {"session_id": session_id, "error": str(exc), "topic": msg.topic}
                try:
                    await producer.send_and_wait(TOPIC_OUT, key=session_id.encode(), value=json.dumps(err_evt).encode())
                except UnknownTopicOrPartitionError:
                    logger.error("memory_events topic missing when emitting error")
                continue
            pid = int(time.time()*1000)
            point = PointStruct(id=pid, vector=vec, payload={"session_id": session_id, "text": text, "ts": time.time(), "topic": msg.topic})
            client.upsert(collection_name=COLLECTION, points=[point])
            evt = {"session_id": session_id, "stored_id": pid, "topic": msg.topic}
            try:
                await producer.send_and_wait(TOPIC_OUT, key=session_id.encode(), value=json.dumps(evt).encode())
            except UnknownTopicOrPartitionError:
                logger.error("memory_events topic missing when emitting success")
            logger.info("Stored embedding for session %s from topic %s", session_id, msg.topic)
    finally:
        await consumer.stop(); await producer.stop()
        logger.info("Memory worker stopped")

app = FastAPI()

@app.get("/health")
async def health():
    return JSONResponse({"ok": True})

@app.get("/ready")
async def ready():
    if not topics_ready:
        raise HTTPException(status_code=503, detail="Kafka topics missing")
    if not worker_task or worker_task.done():
        raise HTTPException(status_code=503, detail="Worker not running")
    return JSONResponse({"ok": True})

@app.on_event("startup")
async def startup_worker():
    global worker_task
    await ensure_topics()
    worker_task = asyncio.create_task(main_loop())

@app.on_event("shutdown")
async def shutdown_worker():
    if worker_task:
        worker_task.cancel()
        with suppress(asyncio.CancelledError):
            await worker_task

if __name__ == "__main__":
    uvicorn.run("worker:app", host="0.0.0.0", port=8000)
