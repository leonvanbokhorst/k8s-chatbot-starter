
import os, json, uuid
from fastapi import FastAPI
from pydantic import BaseModel
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from sse_starlette.sse import EventSourceResponse

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC_IN = "user_messages"
TOPIC_OUT = "model_responses"

app = FastAPI()
producer = None

class ChatIn(BaseModel):
    session_id: str
    text: str

@app.on_event("startup")
async def startup():
    global producer
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    await producer.start()

@app.on_event("shutdown")
async def shutdown():
    if producer:
        await producer.stop()

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/api/chat")
async def chat(msg: ChatIn):
    key = msg.session_id.encode()
    payload = json.dumps({"session_id": msg.session_id, "text": msg.text, "id": str(uuid.uuid4())}).encode()
    await producer.send_and_wait(TOPIC_IN, value=payload, key=key)
    return {"status": "queued", "session_id": msg.session_id}

@app.get("/api/stream")
async def stream(session_id: str):
    # dedicated consumer group per connection
    group = f"gw-{uuid.uuid4()}"
    consumer = AIOKafkaConsumer(
        TOPIC_OUT,
        bootstrap_servers=BOOTSTRAP,
        group_id=group,
        enable_auto_commit=True,
        auto_offset_reset="latest",
    )
    await consumer.start()

    async def gen():
        try:
            async for msg in consumer:
                try:
                    val = json.loads(msg.value.decode())
                except Exception:
                    continue
                if val.get("session_id") == session_id:
                    yield {"event": "message", "data": json.dumps(val)}
        finally:
            await consumer.stop()

    return EventSourceResponse(gen())
