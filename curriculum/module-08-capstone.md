# Module 08 — Capstone Chatbot Stack

## Why this matters

All previous modules were sparring practice. Now you assemble the full dojo chatbot: gateway API, Kafka topics, responder worker with an LLM, and memory worker pushing embeddings into Qdrant. Completing this module means you can blueprint and operate a modern event-driven AI system on Kubernetes.

## Learning Objectives

- Design the architecture: ingress → gateway → Kafka → workers → Qdrant.
- Deploy multiple services (Deployments, Services, ConfigMaps, Secrets) that communicate via Kafka.
- Integrate an LLM backend (Ollama, vLLM, or cloud API) within the cluster.
- Stream responses back to a frontend via long polling or server-sent events.
- Observe the system in action and debug failures end-to-end.

## Architecture Recap

- `gateway` Deployment (FastAPI)
- `responder` worker Deployment
- `memory` worker Deployment
- `ollama` Deployment with PVC for models
- Kafka topics: `user_messages`, `model_responses`, `memory_events`
- Qdrant Deployment + Service (from Module 07)
- Ingress exposing `gateway`

## Pre-flight Checklist

- Modules 01–07 completed (especially Kafka/Qdrant running in `lab` namespace).
- LLM model pulled into Ollama image or accessible via network.
- Secrets containing API keys or credentials created (even if placeholder for lab).

## Hands-On Build Steps

1. Deploy LLM backend

   - Use provided `k8s/ollama.yaml` or craft your own.
   - Ensure PVC for model cache; port-forward and test `curl http://localhost:11434/api/tags`.

2. Gateway API

   - Ensure `services/gateway` image built/pushed.
   - Deploy via `k8s/gateway.yaml` with ConfigMap/Secret for Kafka bootstrap servers.
   - Routes: `POST /chat` (publish to Kafka), `GET /stream` (consume responses), `GET /health`.

3. Kafka topics

   - Create topics using `kcat`/`rpk` or Strimzi Topic custom resources.
   - Set partitions=1 for simplicity; replication=1 in dev.

4. Responder worker

   - Deploy `k8s/responder.yaml`, referencing the same ConfigMap/Secret.
   - Worker loop: consume `user_messages`, call Ollama/vLLM, publish to `model_responses`.
   - Configure CPU/memory requests—they spike during inference.

5. Memory worker

   - Deploy `k8s/memory.yaml`.
   - Consumes both `user_messages` and `model_responses`, computes embeddings, upserts into Qdrant.
   - Confirm access to Qdrant service.

6. Ingress & frontend test

   - Apply `k8s/ingress.yaml` targeting `gateway`.
   - Update `/etc/hosts` with `chat.local.test` pointing at ingress IP/port.
   - `curl` or simple web client to hit `/chat` and `/stream`.

7. Observe end-to-end flow

   - Use `kubectl logs -f deployment/responder` to watch message consumption.
   - Tail `gateway` logs while sending messages.
   - Verify Qdrant contains stored embeddings via API.

8. Chaos/resilience drills
   - Delete responder pod mid-conversation; ensure Deployment recreates and resume.
   - Restart Kafka pod and confirm reconnect logic.
   - Scale `gateway` and `responder` to 2 replicas and monitor offset management.

## Checkpoint

- You can run a full conversation through the system and stream responses back.
- You can explain each component’s responsibility and failure modes.
- You have logs or screenshots proving Qdrant stores interaction memory.

## Stretch Goals

- Implement streaming responses via Server-Sent Events or WebSockets in the gateway.
- Add authentication (JWT) to `POST /chat`.
- Integrate KEDA to autoscale based on Kafka lag.
- Swap Ollama for a remote OpenAI endpoint and manage API keys via Secrets.
- Add CI pipeline steps to build/push images and run `kubectl diff`.

## Resources

- Ollama Kubernetes guides — https://github.com/jmorganca/ollama/tree/main/docs/kubernetes
- Kafka consumer patterns — https://kafka.apache.org/documentation/
- Qdrant client examples — https://qdrant.tech/documentation/quick_start/
- SSE in FastAPI — https://fastapi.tiangolo.com/advanced/custom-response/#server-sent-events

## Deliverable

- Working chatbot accessible via ingress, with transcripts showing Kafka-driven flow.
- Capstone demo recording or written walkthrough.
- Retrospective: what you’d change for production (managed Kafka? multi-region? autoscale?).

Congratulations, Little Wan. Master Lonn declares you a certified AI-dojo Cloud Whisperer.
