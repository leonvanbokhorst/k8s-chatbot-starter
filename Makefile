
REGISTRY?=local
VERSION?=0.1.0
NS=lab

IMAGES=gateway responder memory
KIND_CLUSTER=lab

.PHONY: kind-up kind-down deps build load apply delete logs

kind-up:
	kind create cluster --name $(KIND_CLUSTER) --config kind/cluster.yaml || true
	kubectl create ns $(NS) || true

kind-down:
	kind delete cluster --name $(KIND_CLUSTER) || true

deps:
	helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
	helm repo add redpanda https://charts.redpanda.com
	helm repo add qdrant https://qdrant.github.io/qdrant-helm
	helm repo update
	helm upgrade --install ingress ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace 	  --set controller.replicaCount=1 	  --set controller.hostNetwork=true 	  --set controller.kind=DaemonSet || true
	helm upgrade --install rp redpanda/redpanda -n $(NS) --create-namespace 	  --set statefulset.replicas=1 || true
	helm upgrade --install qdrant qdrant/qdrant -n $(NS) || true

build:
	for img in $(IMAGES); do \
	  docker build -t $$img:$(VERSION) services/$$img ; \
	done

load:
	for img in $(IMAGES); do \
	  kind load docker-image $$img:$(VERSION) --name $(KIND_CLUSTER); \
	done

apply:
	kubectl -n $(NS) apply -f k8s/config.yaml
	kubectl -n $(NS) apply -f k8s/gateway.yaml
	kubectl -n $(NS) apply -f k8s/responder.yaml
	kubectl -n $(NS) apply -f k8s/memory.yaml
	kubectl -n $(NS) apply -f k8s/ingress.yaml

delete:
	kubectl -n $(NS) delete -f k8s/ingress.yaml --ignore-not-found
	kubectl -n $(NS) delete -f k8s/memory.yaml --ignore-not-found
	kubectl -n $(NS) delete -f k8s/responder.yaml --ignore-not-found
	kubectl -n $(NS) delete -f k8s/gateway.yaml --ignore-not-found
	kubectl -n $(NS) delete -f k8s/config.yaml --ignore-not-found

logs:
	kubectl -n $(NS) logs -l app=gateway -f --tail=100
