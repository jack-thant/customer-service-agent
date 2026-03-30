# Service AI

Service AI is a full-stack customer support assistant that combines retrieval-augmented chat, operational tools, mistake-driven self-improvement, and manager-driven agent generation.

## Goals

- Answer customer questions from a configurable knowledge base URL
- Handle operational intents with tools:
  - Card application status checks
  - Failed transaction checks (with transaction ID follow-up)
- Let managers update behavior through editable guidelines
- Let users report wrong answers and feed those reports into automatic fix logic
- Let managers upload documents and generate an instruction-driven agent

## Features

- Customer chat interface with source-backed responses
- Route-aware handling for application status and failed transactions
- Config UI for knowledge base URL and additional guidelines
- Knowledge base ingestion pipeline into ChromaDB
- Mistake reporting dialog directly from assistant responses
- Mistake management UI with status lifecycle (`open`, `patched`, `fixed`, `archived`)
- Automatic guideline/spec patching from reported mistakes
- Agent Studio workflow:
  - Upload docs
  - Refine instructions via manager chat
  - Build indexed agent versions
  - Activate versions
  - Chat with active generated agent

## Project Docs

- Frontend setup and usage: [frontend/README.md](frontend/README.md)
- Backend setup and usage: [backend/README.md](backend/README.md)

## Repository Structure

```text
.
├── frontend/    # Next.js app
└── backend/     # FastAPI API + ingestion + agent pipeline
```

## Deployments
The frontend is deployed on Vercel, while the FastAPI backend is hosted on Render.
Due to Render’s free tier limitations, the backend may experience a cold start delay of up to ~50 seconds after periods of inactivity.

If you notice delays when interacting with the application, this is likely due to the backend service waking up.
