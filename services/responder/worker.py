
import os, json, asyncio, time
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import httpx

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("MODEL", "llama3.1:8b-instruct-q4_K_M")
TOPIC_IN = "user_messages"
TOPIC_OUT = "model_responses"

async def llm_complete(text: str) -> str:
    # Try Ollama... fall back to echo if unavailable
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{OLLAMA_URL}/api/generate", json={"model": MODEL, "prompt": text, "stream": False})
            if r.status_code == 200:
                data = r.json()
                return (data.get("response") or "").strip() or f"[echo] {text}"
    except Exception:
        pass
    return f"[stubbed LLM] You said: {text} ... answering without a real model."

async def main():
    consumer = AIOKafkaConsumer(TOPIC_IN, bootstrap_servers=BOOTSTRAP, group_id="responder")
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
            reply = await llm_complete(text)
            out = {"session_id": session_id, "text": reply, "ts": time.time()}
            await producer.send_and_wait(TOPIC_OUT, key=session_id.encode(), value=json.dumps(out).encode())
    finally:
        await consumer.stop(); await producer.stop()

if __name__ == "__main__":
    asyncio.run(main())
