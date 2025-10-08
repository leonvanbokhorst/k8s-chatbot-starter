# Module 03 — Local Cluster & Tooling

## Why this matters

Knowing Kubernetes theory without cluster reps is like practicing sword forms without hitting the dummy. This module sets up your local dojo—kind, k3d, or minikube—so you deploy, scale, and observe like a battle-hardened SRE.

## Learning Objectives

- Install and configure a local Kubernetes cluster tool (kind/k3d/minikube).
- Use `kubectl` fluently: contexts, namespaces, applies, deletes, logs.
- Install Helm and deploy charts.
- Manage namespaces for isolated environments.
- Observe cluster events and understand pod lifecycle states.

## Prerequisite Check

- Modules 01 & 02 manifests ready.
- Docker Desktop or container runtime enabled.
- `kubectl` in PATH.

## Core Concepts

- **kubeconfig & contexts**: switching clusters effortlessly.
- **Namespaces**: logical separators for workloads.
- **kubectl verbs**: `get`, `describe`, `logs`, `apply`, `delete`, `scale`.
- **Helm**: templating + release management.
- **Events & troubleshooting**: `kubectl describe` reveals why pods break.

## Hands-On Drills

1. Stand up a cluster

   ```bash
   kind create cluster --name lab
   kubectl cluster-info --context kind-lab
   ```

   - If using k3d: `k3d cluster create lab`.
   - Confirm nodes: `kubectl get nodes -o wide`.

2. Namespace rituals

   ```bash
   kubectl create namespace lab
   kubectl config set-context --current --namespace lab
   kubectl get ns
   ```

3. Deploy your app

   ```bash
   kubectl apply -f k8s/gateway.yaml
   kubectl get pods
   kubectl describe pod <pod-name>
   ```

4. Scale and observe

   ```bash
   kubectl scale deployment gateway --replicas=3
   kubectl get pods -w
   ```

   - Delete a pod: `kubectl delete pod <pod-name>`; watch rescheduling.

5. Logs & exec

   ```bash
   kubectl logs deployment/gateway
   kubectl logs -f deployment/gateway
   kubectl exec deployment/gateway -- curl -s localhost:8000/health
   ```

6. Clean up
   ```bash
   kubectl delete -f k8s/gateway.yaml
   kind delete cluster --name lab
   ```

## Checkpoint

- You can recreate a cluster from scratch in minutes.
- You can explain the difference between deleting a pod vs a deployment.
- You’re comfortable tailing logs and describing resources.

## Stretch Goals

- Try k3d with a custom `--servers`/`--agents` topology.
- Set up `kubectx`/`kubens` for faster context switching.
- Install a simple Helm chart (e.g., `helm install metrics stable/metrics-server`).
- Use `kubectl top pods` after enabling metrics-server.

## Resources

- kind quick start — https://kind.sigs.k8s.io/docs/user/quick-start/
- kubectl cheatsheet — https://kubernetes.io/docs/reference/kubectl/cheatsheet/
- Helm docs — https://helm.sh/docs/intro/quickstart/

## Deliverable

- Reproducible steps (script or Makefile targets) to create/destroy the cluster and deploy your app.
- Journal notes capturing the difference between Pod phases and your debug process.

Your cluster muscle memory is forming. Master Lonn senses fewer faceplants in your future.
