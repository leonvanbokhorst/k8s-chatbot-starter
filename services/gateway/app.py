
import os, json, uuid, logging
from contextlib import suppress
from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import UnknownTopicOrPartitionError, TopicAlreadyExistsError
from sse_starlette.sse import EventSourceResponse
from logging.handlers import RotatingFileHandler

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC_IN = os.getenv("TOPIC_IN", "user_messages")
TOPIC_OUT = os.getenv("TOPIC_OUT", "model_responses")
MEMORY_TOPIC = os.getenv("MEMORY_TOPIC", "memory_events")
APP_GREETING = os.getenv("APP_GREETING", "Welcome to the dojo")
LOG_PATH = os.getenv("GATEWAY_LOG_PATH", os.getenv("LOG_PATH", "/var/log/app/gateway.log"))
REQUIRED_TOPICS: List[str] = sorted({TOPIC_IN, TOPIC_OUT, MEMORY_TOPIC})

logger = logging.getLogger("gateway")
logger.setLevel(logging.INFO)
if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)
    if LOG_PATH:
        path = Path(LOG_PATH)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(path, maxBytes=5 * 1024 * 1024, backupCount=3)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as exc:
            logger.warning("Failed to initialize file logger at %s: %s", path, exc)

topics_ready = False
app = FastAPI()
producer = None

class ChatIn(BaseModel):
    session_id: str
    text: str

async def ensure_topics():
    global topics_ready
    admin = AIOKafkaAdminClient(bootstrap_servers=BOOTSTRAP)
    try:
        existing = await admin.list_topics()
        missing = [name for name in REQUIRED_TOPICS if name not in existing]
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

@app.on_event("startup")
async def startup():
    global producer
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    await producer.start()
    await ensure_topics()
    logger.info("Gateway startup complete")

@app.on_event("shutdown")
async def shutdown():
    if producer:
        await producer.stop()
    logger.info("Gateway shutdown complete")

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/ready")
async def ready():
    if not producer or producer._closed:
        raise HTTPException(status_code=503, detail="Kafka producer not ready")
    if not topics_ready:
        raise HTTPException(status_code=503, detail="Kafka topics missing")
    return {"ok": True}

INDEX_HTML = """
<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>Dojo Chat</title>
    <style>
      body { font-family: system-ui, sans-serif; margin: 2rem; background: #0f172a; color: #f8fafc; }
      h1 { margin-bottom: 1rem; }
      .container { max-width: 720px; }
      #log { margin-top: 1.5rem; padding: 1rem; background: #1e293b; border-radius: 8px; height: 45vh; overflow-y: auto; }
      label, input, textarea, button { font-size: 1rem; }
      textarea { width: 100%; height: 6rem; margin-bottom: 0.75rem; padding: 0.5rem; border-radius: 4px; border: 1px solid #334155; background: #0f172a; color: #f8fafc; }
      input { width: 100%; margin-bottom: 0.75rem; padding: 0.5rem; border-radius: 4px; border: 1px solid #334155; background: #0f172a; color: #f8fafc; }
      button { background: #38bdf8; color: #0f172a; border: none; padding: 0.6rem 1rem; border-radius: 4px; cursor: pointer; font-weight: 600; }
      button:disabled { opacity: 0.5; cursor: not-allowed; }
      .event { margin-bottom: 0.75rem; padding-bottom: 0.5rem; border-bottom: 1px solid #334155; }
      .event span { display: block; }
      .event .meta { font-size: 0.8rem; color: #94a3b8; margin-bottom: 0.25rem; }
    </style>
  </head>
  <body>
    <div class=\"container\">
      <h1>Secret Dojo Chat</h1>
      <p>Send a message to the LLM via Kafka and watch responses flow back.</p>
      <label for=\"session\">Session ID</label>
      <input id=\"session\" value=\"demo\" />
      <label for=\"message\">Message</label>
      <textarea id=\"message\" placeholder=\"Ask the dojo...\"></textarea>
      <button id=\"send\">Send</button>
      <div id=\"log\"></div>
    </div>
    <script>
      const log = document.getElementById('log');
      const sendBtn = document.getElementById('send');
      const messageEl = document.getElementById('message');
      const sessionEl = document.getElementById('session');
      let source;
      function addEvent(label, payload) {
        const wrapper = document.createElement('div');
        wrapper.className = 'event';
        const meta = document.createElement('span');
        meta.className = 'meta';
        meta.textContent = label;
        const body = document.createElement('span');
        body.textContent = payload;
        wrapper.appendChild(meta);
        wrapper.appendChild(body);
        log.appendChild(wrapper);
        log.scrollTop = log.scrollHeight;
      }
      function attachStream(sessionId) {
        if (source) source.close();
        source = new EventSource(`/stream?session_id=${encodeURIComponent(sessionId)}`);
        source.onmessage = (evt) => addEvent('model_responses', evt.data);
        source.onerror = () => {
          addEvent('system', 'Stream disconnected');
          source.close();
        };
      }
      sendBtn.addEventListener('click', async () => {
        const sessionId = sessionEl.value.trim();
        const text = messageEl.value.trim();
        if (!sessionId || !text) {
          addEvent('system', 'Session ID and message are required');
          return;
        }
        sendBtn.disabled = true;
        try {
          const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, text })
          });
          if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: res.statusText }));
            addEvent('error', JSON.stringify(err));
          } else {
            const data = await res.json();
            addEvent('user_messages', JSON.stringify(data));
            attachStream(sessionId);
          }
        } catch (err) {
          addEvent('error', err.message || err);
        } finally {
          sendBtn.disabled = false;
          messageEl.value = '';
        }
      });
    </script>
  </body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return INDEX_HTML

@app.get("/hello")
async def hello():
    return {"message": APP_GREETING}

@app.post("/chat")
async def chat(msg: ChatIn):
    key = msg.session_id.encode()
    payload = json.dumps({"session_id": msg.session_id, "text": msg.text, "id": str(uuid.uuid4())}).encode()
    try:
        await producer.send_and_wait(TOPIC_IN, value=payload, key=key)
    except UnknownTopicOrPartitionError as exc:
        logger.error("Topic missing when sending message: %s", exc)
        raise HTTPException(status_code=503, detail="Kafka topic not ready") from exc
    logger.info("Queued message for session %s", msg.session_id)
    return {"status": "queued", "session_id": msg.session_id}

@app.get("/stream")
async def stream(session_id: str):
    group = f"gw-{uuid.uuid4()}"
    consumer = AIOKafkaConsumer(
        TOPIC_OUT,
        bootstrap_servers=BOOTSTRAP,
        group_id=group,
        enable_auto_commit=True,
        auto_offset_reset="latest",
    )
    try:
        await consumer.start()
    except UnknownTopicOrPartitionError as exc:
        logger.error("Topic missing when starting stream: %s", exc)
        raise HTTPException(status_code=503, detail="Kafka topic not ready") from exc

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
            with suppress(Exception):
                await consumer.stop()

    return EventSourceResponse(gen())
