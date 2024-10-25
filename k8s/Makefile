# Variables
APP_NAME := demo-llm-app
DOCKER_IMAGE := $(APP_NAME):latest
KUBE_NAMESPACE := default
HELM_RELEASE := $(APP_NAME)
CHROMADB_RELEASE := chroma
SPLUNK_CLUSTER_NAME := docker-demo-llm-app
SPLUNK_REALM := us1
ENVIRONMENT := test

# Validate required environment variables
ifndef OPENAI_API_KEY
$(error "OPENAI_API_KEY is undefined. Please export it before running this command.")
endif

ifndef SPLUNK_OBSERVABILITY_ACCESS_TOKEN
$(error "SPLUNK_OBSERVABILITY_ACCESS_TOKEN is undefined. Please export it before running this command.")
endif

.PHONY: all build run-docker setup-metrics install-splunk-otel-collector patch-splunk-config install-redis install-chromadb create-openai-secret deploy-app test clean

# Default target
all: build setup-metrics install-splunk-otel-collector patch-splunk-config install-redis install-chromadb create-openai-secret deploy-app

# Build the Docker image
build:
	docker build -t $(DOCKER_IMAGE) .

# Optionally run the Docker image locally
run-docker:
	docker run -p 8080:8080 -e OPENAI_API_KEY=$(OPENAI_API_KEY) $(DOCKER_IMAGE)

# Set up Kubernetes metrics components
setup-metrics:
	helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
	helm upgrade --install metrics-server metrics-server/metrics-server --set args="{--kubelet-insecure-tls}"
	@echo "Waiting for Metrics Server to be ready..."
	#kubectl rollout status deployment/metrics-server -n kube-system
	kubectl top node || true

# Install Splunk OpenTelemetry Collector via Helm
install-splunk-otel-collector:
	helm repo add splunk-otel-collector-chart https://signalfx.github.io/splunk-otel-collector-chart
	helm repo update
	helm install splunk-otel-collector \
		--set="splunkObservability.accessToken=$(SPLUNK_OBSERVABILITY_ACCESS_TOKEN),clusterName=$(SPLUNK_CLUSTER_NAME),splunkObservability.realm=$(SPLUNK_REALM),gateway.enabled=false,splunkObservability.profilingEnabled=true,environment=$(ENVIRONMENT),operator.enabled=true,certmanager.enabled=true,agent.discovery.enabled=true" \
		splunk-otel-collector-chart/splunk-otel-collector --version 0.111.0

# TODO: Patch Splunk configuration to enable Redis receiver
#patch-splunk-config:
#	kubectl apply -f splunk-otel-collector-otel-k8s-cluster-receiver.configmap.yaml
#	kubectl rollout restart daemonset.apps/splunk-otel-collector-agent
#	kubectl rollout restart deployment.apps/splunk-otel-collector-k8s-cluster-receiver

# Install Redis deployment
install-redis:
	kubectl apply -f redis-deployment.yaml

# Install ChromaDB via Helm
install-chromadb:
	helm repo add chroma https://amikos-tech.github.io/chromadb-chart/
	helm install $(CHROMADB_RELEASE) chroma/chromadb --set chromadb.allowReset="true"

# Create Kubernetes secret for OpenAI API key
create-openai-secret:
	kubectl create secret generic openai-secret --from-literal=api_key=$(OPENAI_API_KEY) --namespace $(KUBE_NAMESPACE) || true

# Deploy the application using Helm
deploy-app:
	#helm install $(HELM_RELEASE) ./demo-llm-app
	kubectl apply -f demo-llm-app-deployment.yaml

# Test the application
test:
	kubectl port-forward service/$(HELM_RELEASE) 8080:8080 &
	sleep 5
	@echo "Sending test request to the application..."
	curl -d '{"question":"Which customers are associated with the company Cherry and Sons?"}' \
		-H "Content-Type: application/json" \
		-X POST http://localhost:8080/askquestion

# Clean up deployed resources
clean:
	kubectl delete -f demo-llm-app-deployment.yaml --ignore-not-found
	helm uninstall $(CHROMADB_RELEASE) || true
	kubectl delete -f redis-deployment.yaml --ignore-not-found
	kubectl delete secret openai-secret --namespace $(KUBE_NAMESPACE) --ignore-not-found
	helm uninstall splunk-otel-collector || true
	kubectl delete -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.7.2/components.yaml --ignore-not-found
	kubectl delete -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.1.0/aio/deploy/recommended.yaml --ignore-not-found
