# Module 02 — Kubernetes Core Objects

## Why this matters

Pods, Deployments, and Services are the kata you repeat until your brain autocompletes YAML in your sleep. We make the FastAPI image from Module 01 production-ish by letting Kubernetes summon, scale, and update it.

## Learning Objectives

- Describe what a Pod is (one or more containers sharing network + storage namespaces).
- Write Deployments that manage Pods, roll updates, and track replica state.
- Define Services (ClusterIP/NodePort/LoadBalancer) and when to use each.
- Use ConfigMaps and Secrets to inject configuration.
- Understand readiness vs liveness probes at the Kubernetes layer.

## Prerequisite Check

- Module 01 container image available in a registry.
- kubectl installed.
- A test cluster (kind/k3d/minikube) or remote sandbox access.

## Core Concepts

- **Pods**: scheduling unit, ephemeral, owned by controllers.
- **ReplicaSet & Deployment**: declarative state, rolling updates, rollout history.
- **Services**: stable endpoints for Pods; selectors vs headless Services.
- **ConfigMaps/Secrets**: environmental wiring for your Pods.
- **Requests/Limits**: CPU/memory constraints to keep nodes happy.

## Hands-On Drills

1. Write your Deployment

   - Base it on the FastAPI image tag from Module 01.
   - Set `replicas: 2`, add labels `app: gateway` (or your app name).
   - Mount env vars via `envFrom` referencing a ConfigMap.

2. Define ConfigMap & Secret

   - `app-config` with `APP_GREETING=Hey dojo`, `KAFKA_BOOTSTRAP`, `OLLAMA_URL`, etc. (mirror `k8s/config.yaml`).
   - `app-secrets` with placeholder `KAFKA_USERNAME`, `KAFKA_PASSWORD` values (OK to leave empty in dev).

3. Craft a Service

   - ClusterIP exposing port 80 → container 8000.
   - Ensure selectors match Deployment labels.

4. Add probes + resources

   - Liveness and readiness hitting `/health`.
   - Requests: `100m` CPU / `128Mi` memory. Limits double that.

5. Apply and inspect

   ```bash
   kubectl apply -f k8s/gateway.yaml
   kubectl get deploy,pods,svc
   kubectl describe deploy gateway
   ```

   - Observe replica rollout and pod status.

6. Trigger rollout
   ```bash
   kubectl set image deploy/gateway app=ghcr.io/<you>/fastapi-hello:0.1.1
   kubectl rollout status deploy/gateway
   kubectl rollout history deploy/gateway
   ```

## Checkpoint

- You can explain the difference between a Pod and Deployment.
- You know how Services provide stable endpoints.
- You can articulate why ConfigMaps and Secrets exist separately.
- You know where probes live and how Kubernetes uses them.

## Stretch Goals

- Use `kubectl diff` to preview changes before applying.
- Experiment with `kubectl rollout undo` to revert an update.
- Add annotations and labels for team ownership and observability.
- Try a headless Service + StatefulSet for curiosity (prep for Module 05).

## Resources

- Kubernetes Concepts — https://kubernetes.io/docs/concepts/
- Deployments walkthrough — https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- Services overview — https://kubernetes.io/docs/concepts/services-networking/service/

## Deliverable

- Working Deployment + Service + ConfigMap + Secret manifests checked into `k8s/`.
- Journal notes capturing rollout observations, plus questions for Master Lonn.

At this point, you’re juggling YAML like a true AI-dojo adept. Onward to owning the cluster itself.
