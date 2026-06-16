# Aegis

![Status](https://img.shields.io/badge/status-active--development-orange)

Multi-agent research synthesis system using LangGraph, Gemini, LlamaIndex, and Pinecone with full LLMOps instrumentation.

**Goal:** Build a production-grade multi-agent pipeline using LangGraph for stateful orchestration; agents autonomously plan, retrieve (LlamaIndex + Pinecone), draft, and self-critique research reports using Gemini. Deployed on AWS (ECS + ECR) with full MLOps instrumentation via LangSmith and MLflow; CI/CD via GitHub Actions + Terraform.

## System Architecture

<img src="docs/system_architecture.png" width="600"/>

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1 - Google AI Studio (Gemini API)](#step-1--google-ai-studio-gemini-api)
3. [Step 2 - Pinecone (Vector Database)](#step-2--pinecone-vector-database)
4. [Step 3 - LangSmith (Observability)](#step-3--langsmith-observability)
5. [Step 4 - Configure Your .env](#step-4--configure-your-env)
6. [Step 5 - Run the Application](#step-5--run-the-application)
7. [Step 6 - Using the API](#step-6--using-the-api)
8. [Tech Stack](#tech-stack)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

To run Aegis you need accounts and API keys from three external services. All have free tiers sufficient for development.

- Google AI Studio account (Gemini API)
- Pinecone account (vector database)
- LangSmith account (tracing & observability)

---

## Step 1 - Google AI Studio (Gemini API)

> **Cost:** Gemini Flash is free up to 15 requests/minute. Gemini Pro also has a free tier. You won't be charged during development if you stay within limits.

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with your Google account
3. Click **Get API key** in the left sidebar
4. Click **Create API key** → select **Create API key in new project**
5. Copy the key - you'll need it in Step 4

---

## Step 2 - Pinecone (Vector Database)

> **Cost:** Free tier gives you 1 index and 2 GB storage - enough for development.

1. Go to [pinecone.io](https://pinecone.io) and sign up for free
2. After login, go to **API Keys** in the left sidebar
3. Copy the default API key
4. Go to **Indexes** → **Create Index** with these settings:

| Setting    | Value         |
| ---------- | ------------- |
| Name       | `aegis-index` |
| Dimensions | `768`         |
| Metric     | `cosine`      |
| Cloud      | AWS           |
| Region     | `us-east-1`   |

---

## Step 3 - LangSmith (Observability)

> **Cost:** Free tier includes 5,000 traces/month - plenty for development.

1. Go to [smith.langchain.com](https://smith.langchain.com) and sign up for free
2. After login, go to **Settings** → **API Keys**
3. Click **Create API Key**
4. Copy the key

---

## Step 4 - Configure Your .env

Copy `.env.example` to `.env` at the project root:

```bash
cp .env.example .env
```

Fill in all the keys you collected above:

```env
GEMINI_API_KEY=your_gemini_key_here
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_INDEX_NAME=aegis-index
LANGCHAIN_API_KEY=your_langsmith_key_here
```

> ⚠️ **Never commit your `.env` file to version control.** It is already listed in `.gitignore`.

---

## Step 5 - Run the Application

Make sure Docker is running, then:

```bash
docker compose up
```

The FastAPI server will be available at `http://localhost:8000`. Access the interactive API docs at:

```
http://localhost:8000/docs
```

---

## Step 6 - Using the API

### Ingest Documents

Before running research queries, ingest your source documents into Pinecone:

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"source": "path/to/your/documents"}'
```

### Run a Research Query

Submit a research question and Aegis will plan sub-questions, retrieve relevant chunks, draft a report, self-critique it, and return a polished final report:

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the key findings on X?"}'
```

The response includes a structured report with citations and an optional PDF download.

---

## Tech Stack

| Layer               | Technology                |
| ------------------- | ------------------------- |
| Orchestration       | LangGraph                 |
| LLMs                | Google Gemini Flash + Pro |
| Retrieval           | LlamaIndex + Pinecone     |
| Tracing             | LangSmith                 |
| Experiment tracking | MLflow                    |
| API                 | FastAPI                   |
| Deployment          | AWS ECS + ECR             |
| IaC                 | Terraform                 |
| CI/CD               | GitHub Actions            |

---

## Project Structure

```text
aegis/
├── .github/workflows/deploy.yml
├── infra/                          # Terraform (managed by DevOps)
├── app/
│   ├── main.py                     # FastAPI entrypoint
│   ├── config.py                   # Pydantic settings
│   ├── api/routes/                 # research.py, ingest.py
│   ├── graph/                      # LangGraph nodes and state
│   ├── retrieval/                  # LlamaIndex + Pinecone pipelines
│   ├── llm/                        # Gemini client and prompts
│   ├── evaluation/                 # Metrics, judge, MLflow logger
│   └── observability/              # LangSmith, structured logging
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Troubleshooting

**API key errors** - Double-check your `.env` file. Keys must have no extra spaces or quotes. Make sure you copied the full key from each service dashboard.

**Pinecone index not found** - Confirm the index name in your `.env` exactly matches what you created in Pinecone (`aegis-index`). Index names are case-sensitive.

**Docker not starting** - Make sure Docker is running on your machine before executing `docker compose up`. On Windows, ensure WSL 2 integration is enabled in Docker Desktop settings.

**Rate limit errors from Gemini** - The free tier allows 15 requests per minute for Gemini Flash. If you hit rate limits, wait a moment and retry.
