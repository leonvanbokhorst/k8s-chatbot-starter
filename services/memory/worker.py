
import os, json, asyncio, math, time, hashlib
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = "chat_memory"
DIM=256

TOPIC_IN_A = "user_messages"
TOPIC_IN_B = "model_responses"
TOPIC_OUT = "memory_events"

def hash_embed(text: str, dim: int = DIM):
    # naive stable hashing embedder
    vec = [0]*dim
    for token in text.lower().split():
        h = int(hashlib.sha1(token.encode()).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1
    norm = math.sqrt(sum(v*v for v in vec)) or 1.0
    return [v / norm for v in vec]

async def main():
    client = QdrantClient(url=QDRANT_URL)
    try:
        client.get_collection(COLLECTION)
    except Exception:
        client.recreate_collection(COLLECTION, vectors_config=VectorParams(size=DIM, distance=Distance.COSINE))

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
            vec = hash_embed(text)
            pid = int(time.time()*1000)
            point = PointStruct(id=pid, vector=vec, payload={"session_id": session_id, "text": text, "ts": time.time(), "topic": msg.topic})
            client.upsert(collection_name=COLLECTION, points=[point])
            evt = {"session_id": session_id, "stored_id": pid, "topic": msg.topic}
            await producer.send_and_wait(TOPIC_OUT, key=session_id.encode(), value=json.dumps(evt).encode())
    finally:
        await consumer.stop(); await producer.stop()

if __name__ == "__main__":
    asyncio.run(main())
