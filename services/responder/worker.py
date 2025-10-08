
import os, json, asyncio, time, logging
from pathlib import Path
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError, UnknownTopicOrPartitionError
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import suppress
from logging.handlers import RotatingFileHandler

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

LOG_PATH = os.getenv("RESPONDER_LOG_PATH", "/var/log/app/responder.log")
logger = logging.getLogger("responder")
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

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("MODEL", "llama3.1:8b-instruct-q4_K_M")
TOPIC_IN = os.getenv("TOPIC_IN", "user_messages")
TOPIC_OUT = os.getenv("TOPIC_OUT", "model_responses")
TOPICS = [TOPIC_IN, TOPIC_OUT]
worker_task = None
producer = None
consumer = None

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

async def llm_complete(text: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{OLLAMA_URL}/api/generate", json={"model": MODEL, "prompt": text, "stream": False})
            if r.status_code == 200:
                data = r.json()
                return (data.get("response") or "").strip() or f"[echo] {text}"
    except Exception as exc:
        logger.warning("LLM request failed: %s", exc)
    return f"[stubbed LLM] You said: {text} ... answering without a real model."

async def worker_loop():
    global consumer, producer
    consumer = AIOKafkaConsumer(TOPIC_IN, bootstrap_servers=BOOTSTRAP, group_id="responder")
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    await consumer.start(); await producer.start()
    logger.info("Responder worker started")
    try:
        async for msg in consumer:
            try:
                data = json.loads(msg.value.decode())
            except Exception:
                continue
            text = data.get("text"," ")
            session_id = data.get("session_id","default")
            reply = await llm_complete(text)
            out = {"session_id": session_id, "text": reply, "ts": time.time()}
            try:
                await producer.send_and_wait(TOPIC_OUT, key=session_id.encode(), value=json.dumps(out).encode())
            except UnknownTopicOrPartitionError as exc:
                logger.error("Output topic missing: %s", exc)
    except asyncio.CancelledError:
        raise
    finally:
        await consumer.stop(); await producer.stop()
        logger.info("Responder worker stopped")

@app.on_event("startup")
async def startup_worker():
    global worker_task
    await ensure_topics()
    worker_task = asyncio.create_task(worker_loop())

@app.on_event("shutdown")
async def shutdown_worker():
    if worker_task:
        worker_task.cancel()
        with suppress(asyncio.CancelledError):
            await worker_task

if __name__ == "__main__":
    uvicorn.run("worker:app", host="0.0.0.0", port=8000)
