# Demo GenAI Cloud-Native App

This application is a simple cloud-native app that demonstrates observability for a Generative AI application deployed in Kubernetes. It also showcases how to use the OpenAI API to generate text, ChromaDB to store embeddings, and Redis for caching.

## Prerequisites

These instructions are for macOS but can be adapted for Linux with minor changes.

- **Docker Desktop**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop) for local Kubernetes development.
- **Make**: Ensure `make` is installed (`xcode-select --install` on macOS).
- **kubectl**: Install [kubectl](https://kubernetes.io/docs/tasks/tools/).
- **Helm**: Install [Helm](https://helm.sh/docs/intro/install/).
- **OpenAI API Key**: Sign up at [OpenAI](https://openai.com/) to obtain an API key.
- **Splunk Observability Access Token**: Sign up at [Splunk Observability](https://www.splunk.com/en_us/observability.html) to obtain an access token.

## Setting Up

The setup process is automated using a `Makefile`. Follow the steps below to deploy the application and its dependencies.

### 1. Export Required Environment Variables

Export your OpenAI API key and Splunk Observability access token:

    export OPENAI_API_KEY=your_openai_api_key
    export SPLUNK_OBSERVABILITY_ACCESS_TOKEN=your_splunk_access_token

### 2. Build and Deploy the Application

Run the following command to build the Docker image, set up metrics, install Splunk OpenTelemetry Collector, deploy Redis and ChromaDB, create the OpenAI secret, and deploy the application:

    make all

### 3. Test the Application

After deployment, you can test the application using:

    make test

This command will:

- Port-forward the application service to `localhost:8080`.
- Send a sample question to the application and display the response.

### 4. Clean Up

To remove all deployed components from your cluster, run:

    make clean

## Additional Makefile Targets

- **`make build`**: Builds the Docker image for the application.
- **`make run-docker`**: Runs the Docker image locally to verify functionality (optional).
- **`make setup-metrics`**: Deploys Kubernetes Metrics Server and Dashboard.
- **`make install-splunk-otel-collector`**: Installs Splunk OpenTelemetry Collector via Helm.
- **`make patch-splunk-config`**: Patches the Splunk configuration to enable the Redis receiver.
- **`make install-redis`**: Deploys Redis using `redis-deployment.yaml`.
- **`make install-chromadb`**: Installs ChromaDB via Helm.
- **`make create-openai-secret`**: Creates a Kubernetes secret with your OpenAI API key.
- **`make deploy-app`**: Deploys your application using Helm.
- **`make test`**: Tests the deployed application.
- **`make clean`**: Uninstalls all deployed components and deletes created resources.

## Notes

- **Environment Variables**: The `Makefile` checks for `OPENAI_API_KEY` and `SPLUNK_OBSERVABILITY_ACCESS_TOKEN`. Ensure these are exported before running the commands.
- **Kubernetes Namespace**: The default namespace is used. Adjust the `KUBE_NAMESPACE` variable in the `Makefile` if you're using a different namespace.
- **Helm Releases**: Release names for Helm charts are defined in the `Makefile` variables `HELM_RELEASE` and `CHROMADB_RELEASE`. Modify them if needed.
- **Splunk Configuration**: The `patch-splunk-config` target applies a custom ConfigMap and restarts the Splunk OpenTelemetry Collector pods.

## Manual Deployment (Optional)

If you prefer to run the commands manually without the `Makefile`, follow these steps:

### Build the Docker Image

    docker build -t demo-llm-app .

### (Optional) Run the Docker Image Locally

    docker run -p 8080:8080 -e OPENAI_API_KEY=$OPENAI_API_KEY demo-llm-app

### Set Up Metrics Components

    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.7.2/components.yaml
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.1.0/aio/deploy/recommended.yaml
    kubectl rollout status deployment/metrics-server -n kube-system
    kubectl top node

### Install Splunk OpenTelemetry Collector

    helm repo add splunk-otel-collector-chart https://signalfx.github.io/splunk-otel-collector-chart
    helm repo update
    helm install splunk-otel-collector \
      --set="splunkObservability.accessToken=$SPLUNK_OBSERVABILITY_ACCESS_TOKEN,clusterName=docker-demo-sergey,splunkObservability.realm=us1,gateway.enabled=false,splunkObservability.profilingEnabled=true,environment=test,operator.enabled=true,certmanager.enabled=true,agent.discovery.enabled=true" \
      splunk-otel-collector-chart/splunk-otel-collector

### Patch Splunk Configuration

    kubectl apply -f splunk-otel-collector-otel-k8s-cluster-receiver.configmap.yaml
    kubectl rollout restart daemonset.apps/splunk-otel-collector-agent
    kubectl rollout restart deployment.apps/splunk-otel-collector-k8s-cluster-receiver

### Install Redis

    kubectl apply -f redis-deployment.yaml

### Install ChromaDB

    helm repo add chroma https://amikos-tech.github.io/chromadb-chart/
    helm repo update
    helm install chroma chroma/chromadb --set chromadb.allowReset="true"

### Create a Secret with Your OPENAI_API_KEY

    kubectl create secret generic openai-secret --from-literal=api_key=$OPENAI_API_KEY

### Deploy the Application

    helm install demo-llm-app ./my-llm-app

### Testing the Application

    kubectl port-forward service/demo-llm-app 8080:8080 &
    curl -d '{"question":"Which customers are associated with the company Cherry and Sons?"}' \
      -H "Content-Type: application/json" \
      -X POST http://localhost:8080/askquestion
