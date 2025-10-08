
import os, json, asyncio, time
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import suppress
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("memory-worker")

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("MEMORY_COLLECTION", "chat_memory")
EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3")
EMBED_DIM = int(os.getenv("EMBED_DIM", "1024"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

TOPIC_IN_A = "user_messages"
TOPIC_IN_B = "model_responses"
TOPIC_OUT = "memory_events"
worker_task = None

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
        logger.info("Using existing Qdrant collection '%s'", COLLECTION)
    except Exception as exc:
        logger.warning("Collection '%s' missing, recreating (%s)", COLLECTION, exc)
        client.recreate_collection(COLLECTION, vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE))

    consumer = AIOKafkaConsumer(TOPIC_IN_A, TOPIC_IN_B, bootstrap_servers=BOOTSTRAP, group_id="memory")
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    await consumer.start(); await producer.start()
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
                # emit failure event and continue
                logger.error("Embedding failed for session %s: %s", session_id, exc)
                err_evt = {"session_id": session_id, "error": str(exc), "topic": msg.topic}
                await producer.send_and_wait(TOPIC_OUT, key=session_id.encode(), value=json.dumps(err_evt).encode())
                continue
            pid = int(time.time()*1000)
            point = PointStruct(id=pid, vector=vec, payload={"session_id": session_id, "text": text, "ts": time.time(), "topic": msg.topic})
            client.upsert(collection_name=COLLECTION, points=[point])
            evt = {"session_id": session_id, "stored_id": pid, "topic": msg.topic}
            await producer.send_and_wait(TOPIC_OUT, key=session_id.encode(), value=json.dumps(evt).encode())
            logger.info("Stored embedding for session %s from topic %s", session_id, msg.topic)
    finally:
        await consumer.stop(); await producer.stop()

app = FastAPI()

@app.get("/health")
async def health():
    return JSONResponse({"ok": True})

@app.on_event("startup")
async def startup_worker():
    global worker_task
    worker_task = asyncio.create_task(main_loop())

@app.on_event("shutdown")
async def shutdown_worker():
    if worker_task:
        worker_task.cancel()
        with suppress(asyncio.CancelledError):
            await worker_task

if __name__ == "__main__":
    uvicorn.run("worker:app", host="0.0.0.0", port=8000)
