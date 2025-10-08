# Module 07 — Data & Messaging on Kubernetes

## Why this matters

The capstone chatbot relies on streaming messages and vector search. Running Kafka (or a Kafka-compatible stack like Redpanda) plus Qdrant in-cluster gives you the muscle memory to orchestrate data services. Short version: you’ll wrangle stateful, noisy neighbors without crying.

## Learning Objectives

- Deploy Kafka or Redpanda via Helm or operator.
- Deploy Qdrant (vector database) with persistent storage.
- Understand Kafka topics, partitions, replication basics.
- Use CLI tools (`kcat`, `rpk`, `qdrant-client`) to publish/consume/test.
- Capture ops tradeoffs for stateful services on Kubernetes.

## Prerequisite Check

- Modules 01–06 complete.
- Storage class identified from Module 05.
- Helm comfortable.

## Core Concepts

- **Kafka vs Redpanda**: protocol-compatible, deployment differences.
- **Operators vs plain Helm**: automation vs simplicity.
- **StatefulSets**: sequential pod identities, volume claim templates.
- **Vector DB**: storing embeddings and search indexes.
- **Security & networking**: internal/external listeners, NodePorts.

## Hands-On Drills

1. Deploy Kafka (Redpanda recommended for local simplicity)

   ```bash
   helm repo add redpanda https://charts.redpanda.com
   helm repo update
   helm install rp redpanda/redpanda -n lab --create-namespace \
     --set statefulset.replicas=1 \
     --set storage.persistentVolume.size=1Gi
   kubectl get pods -n lab
   ```

   - For Strimzi alternative: install operator, apply Kafka CR (optional stretch).

2. Deploy Qdrant

   ```bash
   helm repo add qdrant https://qdrant.github.io/qdrant-helm
   helm repo update
   helm install qdrant qdrant/qdrant -n lab \
     --set replicaCount=1 \
     --set persistence.size=1Gi
   kubectl get pods -n lab
   ```

3. Validate Kafka

   ```bash
   kubectl port-forward svc/rp 9092:9092 -n lab
   kcat -b localhost:9092 -L
   kcat -b localhost:9092 -t dojo-test -P <<<'hello from the dojo'
   kcat -b localhost:9092 -t dojo-test -C -o beginning -e
   ```

   - For Redpanda: use `rpk topic create dojo-test`.

4. Validate Qdrant

   ```bash
   kubectl port-forward svc/qdrant 6333:6333 -n lab
   curl -X GET http://localhost:6333/collections
   ```

   - Use Python client to create a test collection and insert embeddings.

5. Capture tradeoffs
   - Note resource usage (`kubectl top pods`), restarts, disk usage.
   - Document when you’d use managed services instead.

## Checkpoint

- You can describe how Kafka topics map to partitions and why replication matters.
- You can explain what Qdrant stores and how embeddings are indexed.
- You’ve produced/consumed a test message and inserted a vector entry.

## Stretch Goals

- Try Strimzi operator with external listeners.
- Add TLS or authentication (SASL) for Kafka.
- Scale Redpanda to 3 replicas and observe leader election.
- Enable Qdrant HNSW index configuration via Helm values.
- Install KEDA and configure a scaled object tied to Kafka lag.

## Resources

- Redpanda docs — https://docs.redpanda.com/
- Strimzi docs — https://strimzi.io/docs/
- Qdrant docs — https://qdrant.tech/documentation/
- Kafka with kcat — https://github.com/edenhill/kcat
- Ollama embeddings API — https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings

## Deliverable

- Working Kafka/Redpanda and Qdrant instances with notes on configuration choices.
- Journal entry listing risks and mitigation strategies for running stateful services in K8s.

Datastream mastery unlocked. Master Lonn gives you the secret nod—time to weave it into the chatbot saga.
