# Monitoring LangChain LLM applications with Splunk Observability Cloud

This repository contains the source code utilized by the 
[Monitoring LangChain LLM applications with Splunk Observability Cloud](https://lantern.splunk.com/Observability/UCE/Unified_Workflows/Enable_Self-Service_Observability/Monitoring_LangChain_LLM_applications_with_Splunk_Observability_Cloud) 
blog article. 

The article starts with a simple Python application that uses OpenAI with GPT 3.5 Turbo to answer questions, 
and then walks through the following improvements: 

* Update the application to use the LangChain framework, which provides many features and benefits that we’ll use throughout the article.
* Use LangChain’s capabilities to ensure context is retained in subsequent requests to OpenAI.
* Modify the application to answer questions from a custom set of data that we provide. To accomplish this, we’ll introduce the concepts of Retrieval-Augmented Generation (RAG), embeddings, and a vector database named Chroma.
* Demonstrate how LangChain makes it easy to switch to another LLM provider such as Google’s Gemini.

These steps are reflected via the different folders of this repository (v1 through v5). 

All versions of the application will generate metrics and traces, so we’ll want to ensure 
an OpenTelemetry collector is running on our machine as well. Refer to [Install and configure the Splunk Distribution of the OpenTelemetry Collector](https://docs.splunk.com/observability/en/gdi/opentelemetry/opentelemetry.html#otel-intro-install)  
for details on installing the collectors.
