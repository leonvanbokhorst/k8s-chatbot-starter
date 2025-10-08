# Tiny k8s Chatbot — Gateway + Responder + Memory with Kafka and Qdrant

This is a minimal, batteries-included starter to run a small chatbot on Kubernetes... local kind cluster... Kafka via Redpanda... Qdrant for vector memory... optional Ollama for the LLM.

## Curriculum

- Training path from container kata to full chatbot stack lives in [`curriculum/README.md`](curriculum/README.md). Eight dojo-style modules lead you through the build.

## Quickstart

```bash
# 0) prerequisites
# - kubectl, kind, helm, docker
# - Python 3.11+ for local dev if you want to run services outside k8s

# 1) create the cluster
make kind-up

# 2) install dependencies (ingress-nginx, redpanda, qdrant)
make deps

# 3) build images and load into kind
make build load

# 4) apply app manifests
make apply

# 5) test the gateway
# send a message
curl -X POST http://chat.local.test/chat -H 'Content-Type: application/json' \
  -d '{"session_id":"demo","text":"Hello from Eindhoven!"}'

# open a stream for responses (Server-Sent Events)... press Ctrl+C to stop
curl -N http://chat.local.test/stream?session_id=demo
```

If you run Ollama locally on your host first... the responder will call it inside the cluster via the `ollama` Service.

```bash
# optional: run ollama inside k8s (pulls a model on first run)
kubectl -n lab apply -f k8s/ollama.yaml
# then:
kubectl -n lab exec deploy/ollama -- ollama pull llama3.1:8b-instruct-q4_K_M
```

## Topics

- `user_messages` — produced by gateway
- `model_responses` — produced by responder... consumed by gateway stream and memory
- `memory_events` — produced by memory when it upserts to Qdrant

## Dev notes

This is a teaching scaffold. The code is intentionally small... async FastAPI + aiokafka... a naive 256-d hashing embedder (works offline)... Qdrant client for storage.

Swap parts as you like:

- Redpanda -> Strimzi, Confluent Cloud
- Qdrant -> pgvector, Milvus
- Ollama -> vLLM, any API
