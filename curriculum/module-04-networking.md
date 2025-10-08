# Module 04 — Networking in Practice

## Why this matters

Pods are useless if nobody can talk to them. This module teaches you to expose services cleanly, compare Service types, and wrangle ingress controllers. You’ll map traffic from your laptop into the cluster like a seasoned traffic engineer.

## Learning Objectives

- Differentiate ClusterIP, NodePort, and LoadBalancer services.
- Deploy an ingress controller (ingress-nginx via Helm).
- Create Ingress resources with host/path rules.
- Configure local DNS overrides using `/etc/hosts` or `dev-tunnels`.
- Debug networking issues with `kubectl port-forward`, logs, and events.

## Prerequisite Check

- Modules 01–03 complete and cluster running.
- Helm installed.

## Core Concepts

- **Service types**: internal-only vs node-exposed vs external LB.
- **Ingress controller vs Ingress resource**: controller handles actual routing.
- **Annotations**: customizing behavior (timeouts, auth, TLS).
- **DNS & hostnames**: mapping friendly names to local IPs.

## Hands-On Drills

1. Deploy ingress-nginx

   ```bash
   helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
   helm repo update
   helm install ingress ingress-nginx/ingress-nginx \
     --namespace ingress-nginx --create-namespace
   kubectl get pods -n ingress-nginx
   ```

2. Create/update Service (ensure ClusterIP exists)

   - Confirm `k8s/gateway.yaml` includes the Service from Module 02.

3. Define Ingress

   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: chat
     namespace: lab
   spec:
     ingressClassName: nginx
     rules:
       - host: chat.local.test
         http:
           paths:
             - path: /
               pathType: Prefix
               backend:
                 service:
                   name: gateway
                   port:
                     number: 80
   ```

   - Apply: `kubectl apply -f k8s/ingress.yaml`.

4. Wire local DNS

   ```bash
   echo "127.0.0.1 chat.local.test" | sudo tee -a /etc/hosts
   kubectl port-forward -n ingress-nginx svc/ingress-ingress-nginx-controller 8080:80
   curl -H "Host: chat.local.test" http://localhost:8080/hello
   ```

   - On k3d/minikube with load balancer addon, you may get an external IP instead.

5. Debugging drills
   - `kubectl describe ingress chat`
   - `kubectl logs -n ingress-nginx deploy/ingress-ingress-nginx-controller`
   - Delete/recreate Service to see how Ingress reacts.

## Checkpoint

- You can articulate when to use NodePort vs Ingress vs LoadBalancer.
- You can hit the service via hostname from your machine.
- You can diagnose common ingress failures (missing Service, wrong port, DNS mismatch).

## Stretch Goals

- Add TLS with a self-signed certificate using cert-manager.
- Route multiple paths/hosts through the same ingress controller.
- Compare ingress-nginx with Traefik or Istio (conceptually).
- Experiment with `kubectl port-forward` directly to a Pod vs Service.

## Resources

- Kubernetes Services — https://kubernetes.io/docs/concepts/services-networking/service/
- Ingress concepts — https://kubernetes.io/docs/concepts/services-networking/ingress/
- ingress-nginx docs — https://kubernetes.github.io/ingress-nginx/

## Deliverable

- Working ingress manifest hosted in `k8s/ingress.yaml` (or equivalent).
- Journal entry capturing how you tested and any anomalies.

Networking kata complete. Master Lonn now grants you access to stateful mysteries.
