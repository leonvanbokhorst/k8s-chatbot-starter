# Secret AI-Dojo Path: Kubernetes + Kafka Chatbot Mastery

Welcome to the dojo, Little Padawan. Master Lonn has sketched the eight sacred scrolls that lead from container basics to a Kubernetes-hosted chatbot with Kafka streaming and a vector memory service. We just translated those vibes into a proper curriculum you can follow, remix, and extend.

## How to Use This

- **Flow linearly**: each module builds on the last. Feel free to revisit earlier drills.
- **Build as you learn**: every module adds a component toward the capstone chatbot.
- **Document your wins**: keep a lab journal with notes, commands, and gotchas.
- **Stretch when ready**: optional challenges help deepen mastery without blocking progress.

## Prerequisites

- Comfortable writing Python or TypeScript/JavaScript services.
- Basic Git workflows and GitHub/registry access.
- Familiarity with REST APIs and HTTP client tools (curl, httpie, Postman).
- Optional but helpful: prior Docker usage and distributed systems intuition.

## Curriculum Map

| Module                                                       | Theme                         | Core Outcome                            |
| ------------------------------------------------------------ | ----------------------------- | --------------------------------------- |
| [01 - Containers & 12-Factor](./module-01-containers.md)     | Container fundamentals        | Containerize and ship a FastAPI service |
| [02 - Kubernetes Core Objects](./module-02-core-objects.md)  | Deployments, Services, Config | Build YAML manifests for your app       |
| [03 - Local Cluster & Tooling](./module-03-local-cluster.md) | Operate a dev cluster         | Deploy, scale, and observe workloads    |
| [04 - Networking in Practice](./module-04-networking.md)     | Ingress & traffic flow        | Expose apps via ingress-nginx           |
| [05 - Storage & State](./module-05-storage.md)               | Stateful workloads            | Run Postgres with persistent volumes    |
| [06 - Observability & Ops](./module-06-observability.md)     | Probing, logging, autoscale   | Instrument and debug workloads          |
| [07 - Data & Messaging](./module-07-data-messaging.md)       | Kafka & Qdrant                | Run Redpanda and a vector DB            |
| [08 - Capstone Chatbot Stack](./module-08-capstone.md)       | Full system integration       | Deploy chatbot gateway, workers, memory |

## Suggested Week-by-Week Pace

- **Week 1**: Modules 01-02
- **Week 2**: Modules 03-04
- **Week 3**: Modules 05-06
- **Week 4**: Modules 07-08 + capstone polish

## Deliverables

- Lab journal with screenshots or terminal captures per module.
- Working Kubernetes manifests in the `k8s/` directory (or your fork).
- Capstone demo: `kubectl port-forward` or ingress-based walkthrough with chat logs.
- Optional blog post or retrospective on what surprised you.

## Toolbelt Checklist

- Docker / Nerdctl
- kubectl & kubeconfig basics
- Helm 3
- kind or k3d (or minikube)
- Python 3.11+ (for FastAPI workers) and Poetry/pip
- Kafka CLI tools (kcat) and vector DB clients
- `make`, `curl`, `jq`, `kubens`

## Mentor Signals

- If you can confidently explain **why** along with **how**, you are dojo-ready.
- Struggling with cluster instability? Pause and review Module 03 drills before moving on.
- Master Lonn expects curiosity: log the questions you couldn’t answer and chase them.

Ready? Crack open Module 01 and start cooking those immutable images.
