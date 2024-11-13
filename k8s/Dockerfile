# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies separately
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Environment variables for OpenTelemetry
ENV OTEL_SERVICE_NAME=my-llm-app
ENV OTEL_RESOURCE_ATTRIBUTES="deployment.environment=test"

# Expose the application on port 8080
EXPOSE 8080

RUN splunk-py-trace-bootstrap

# Define entrypoint and default command
ENTRYPOINT ["splunk-py-trace"]
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]