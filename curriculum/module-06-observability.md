# Module 06 — Observability & Operations

## Why this matters

Even perfect YAML melts when the cluster mood swings. Observability keeps you calm, while probes, logs, and autoscalers handle the chaos. This module turns you into the operator Master Lonn trusts with the dojo keys.

## Learning Objectives

- Configure liveness and readiness probes properly.
- Stream logs, exec into pods, and interpret `kubectl describe` output.
- Use `kubectl top` (with metrics-server) to view resource usage.
- Configure a HorizontalPodAutoscaler (HPA) on CPU metrics.
- Explore event streams for rapid troubleshooting.

## Prerequisite Check

- Modules 01–05 completed.
- metrics-server installed (`kubectl top nodes` succeeds). For kind, use community manifests or `kind` extra configs.

## Core Concepts

- **Probes**: liveness (restart me) vs readiness (not ready yet) vs startup probes.
- **Logging**: stdout/stderr, structured logs, centralized aggregation.
- **Events**: Kubernetes reasons for state changes.
- **Autoscaling**: HPA scales Deployments based on metrics.

## Hands-On Drills

1. Tune probes & resources

   - Update `k8s/gateway.yaml`, `k8s/responder.yaml`, and `k8s/memory.yaml` to include readiness/liveness probes and resource requests/limits.
   - New readiness endpoint `/ready` checks Kafka connectivity and worker state; liveness remains `/health`.

2. Stream logs & exec

   ```bash
   kubectl logs deploy/gateway -f
   kubectl exec deploy/gateway -- env | grep APP
   ```

   - Pods also write rotating logs under `/var/log/app/` (e.g., `gateway.log`, `responder.log`, `memory.log`) for deeper inspection (`kubectl exec` + `tail`).

3. Watch events

   ```bash
   kubectl get events --sort-by=.metadata.creationTimestamp
   kubectl describe deploy/gateway
   ```

4. Install metrics-server (if not present)

   ```bash
   kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
   kubectl top pods -n lab
   ```

5. Configure HPA

   ```bash
   kubectl autoscale deployment gateway --cpu-percent=50 --min=1 --max=5
   kubectl get hpa
   ```

   - Generate load (hey, vegeta, autocannon) to watch scaling.

6. Cleanup
   ```bash
   kubectl delete hpa gateway
   ```

## Checkpoint

- You can explain when to use readiness vs liveness.
- You can tail logs, exec commands, and inspect events.
- You know how HPAs use metrics to scale Deployments.

## Stretch Goals

- Install KEDA and configure scaling on Kafka lag (prep for Module 07/08).
- Configure a simple Prometheus + Grafana stack via Helm and build a dashboard.
- Explore OpenTelemetry instrumentation in the FastAPI service.
- Experiment with `stern` or `kubetail` for multi-pod log tailing.

## Resources

- Probes documentation — https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes
- Horizontal Pod Autoscaler — https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- metrics-server install guide — https://github.com/kubernetes-sigs/metrics-server

## Deliverable

- Screenshots or logs showing probe status, `kubectl top`, and HPA scaling events.
- Journal notes describing a simulated outage and how you diagnosed it.

Your observability senses shimmer. Master Lonn grins—you’re ready to host real data pipelines.
