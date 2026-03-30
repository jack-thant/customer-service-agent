# Service AI Backend

FastAPI backend for **Service AI**. It powers:

- Customer support chat with RAG context
- Knowledge base ingestion from help center category URLs
- Config management for KB URL and behavior guidelines
- Mistake reporting and auto-fix workflow
- Agent build/runtime APIs (document upload, build jobs, spec activation, agent chat)

## Tech Stack

- Python 3.12
- FastAPI + Uvicorn
- SQLAlchemy
- PostgreSQL (Neon)
- ChromaDB (vector storage)
- OpenAI API (embeddings + generation)
- BeautifulSoup + Requests (web ingestion)
- AWS S3 (uploaded document storage)

## Prerequisites

- Python 3.12+
- pip
- OpenAI API key
- Chroma credentials
- Neon PostgreSQL connection URL
- AWS S3 bucket + credentials (required for `/agent/docs`)

## Environment Variables

Create `backend/.env` with the following:

```bash
OPENAI_API_KEY=your_openai_api_key
EMBEDDING_MODEL=text-embedding-3-small

CHROMA_API_KEY=your_chroma_api_key
CHROMA_TENANT=your_chroma_tenant
CHROMA_DATABASE=your_chroma_database
CHROMA_COLLECTION_NAME=atome_kb

# Neon Postgres
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>/<db>?sslmode=require

REQUEST_TIMEOUT_SECONDS=20
MAX_ARTICLE_LINKS=1000
CHUNK_SIZE=1200
CHUNK_OVERLAP=200

AWS_REGION=ap-southeast-2
AWS_S3_BUCKET=your_bucket_name
AWS_S3_PREFIX=agent-uploads
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

## Install and Run

From `backend/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Core Endpoints

- `GET /` health/info message
- `GET /health`
- `POST /chat`
- `GET /config`
- `PUT /config`
- `POST /config/reingest`
- `POST /ingest/category`
- `GET /ingest/debug/search` (debug helper)
- `POST /mistakes`
- `GET /mistakes`
- `PATCH /mistakes/{mistake_id}`
- `POST /agent/docs`
- `POST /agent/build`
- `GET /agent/build/{job_id}`
- `POST /agent/meta-chat`
- `GET /agent/spec/active`
- `GET /agent/specs`
- `POST /agent/spec/{version}/activate`
- `POST /agent/chat`

## Ingestion Flow (Help Center URL)

`POST /config/reingest` (or `POST /ingest/category`) triggers category ingestion.

Current ingestion behavior:

- Discovers article URLs from both category HTML and inline links
- Expands category -> sections -> section articles via API
- De-duplicates and normalizes URLs before ingesting
- Parses article body text and chunks it
- Embeds chunks and upserts into Chroma with metadata

## Mistake Report -> Auto Fix Flow

When the user reports a mistake through `POST /mistakes`, backend flow is:

1. Route creates a mistake record (`MistakeService.create_mistake`).
2. `AutoFixService.process_mistake` is triggered immediately.
3. The service checks runtime:
   - `part1` (main chat assistant): patch config guidelines.
   - `part2` (generated agent): patch active/target agent spec instructions.

### Part 1 (Main Chat) auto-fix logic

1. Load current config (`kb_url`, `additional_guidelines`).
2. Use LLM to generate structured analysis JSON:
   - `root_cause`
   - `suggested_fix`
3. Convert suggestion into a concise instruction patch.
4. Append patch under `## Learned fixes` in config guidelines.
5. Save updated config via `ConfigService.update_config`.
6. Mark mistake as `patched` with analysis + applied fix.
7. Rerun original user question through chat service.
8. Evaluate whether new answer is improved.
9. Final status:
   - `fixed` if improved
   - otherwise remains `patched`

### Part 2 (Generated Agent) auto-fix logic

1. Resolve active spec (or use `mistake.agent_spec_version`).
2. Generate `root_cause` + `suggested_fix` with LLM.
3. Append fix to target spec instructions (`append_fix_to_version`).
4. Update mistake with analysis and applied fix.
5. Mark as `fixed` (or `patched` if no patch target exists).

## Agent Build Flow (Upload Docs + Instructions)

This is the flow used by `/agent/docs`, `/agent/build`, and runtime `/agent/chat`.

### A) Upload document (`POST /agent/docs`)

1. Validate extension (`.txt`, `.md`, `.html`, `.htm`, `.pdf`) and max size (5 MB).
2. Read file bytes and compute SHA-256 checksum.
3. If checksum already exists and S3 object exists, reuse existing record.
4. Otherwise upload file to S3 and store metadata in `knowledge_documents` table.
5. Initial document status is `uploaded`.

### B) Build agent (`POST /agent/build`)

1. Convert manager `instruction_goal` into operational instructions using `AgentMetaService`.
2. Create new agent spec with status `building`.
3. Create ingestion job (`queued`) linked to that spec version.
4. Start background thread for build execution.

Background build thread does:

1. Set job status to `running`.
2. Create/get Chroma collection `agent_v{spec_version}`.
3. For each selected document:
   - Read from S3 (extract text for PDF/HTML/text)
   - Chunk text
   - Create embeddings
   - Upsert chunks into `agent_v{spec_version}` with metadata
   - Mark doc `processed` (or `failed` on error)
   - Increment `processed_docs`
4. After all docs:
   - Mark spec status `ready`
   - Activate this spec version
   - Mark job `completed`
5. If any fatal build error occurs:
   - Mark spec `failed`
   - Mark job `failed` with error summary

### C) Runtime chat (`POST /agent/chat`)

1. Fetch currently active spec.
2. Query matching Chroma collection `agent_v{active_version}`.
3. Retrieve top context chunks for user message.
4. Build system prompt from base policy + active spec instructions.
5. Generate final answer using LLM and return answer + sources.

## Database

Tables are initialized automatically on startup (`init_db()` in app lifespan).

Production database in this project is Neon PostgreSQL via `DATABASE_URL`.

## Docker

A backend Dockerfile is available at `backend/Dockerfile`.

Build and run from repository root:

```bash
docker build -t service-ai-backend ./backend
docker run --rm -p 8000:8000 --env-file backend/.env service-ai-backend
```

## Project Structure

```text
backend/
  app/
    api/routes/          # FastAPI route modules
    core/                # Settings, clients, prompts
    db/                  # SQLAlchemy engine/session/init
    models/              # ORM models
    repositories/        # Data access layer
    schemas/             # Pydantic request/response models
    services/            # Business logic
    requirements.txt
```

## Notes
- The messages chat threads through the agent or meta-agent are not saved in database.
- For the enquiry of card application, the mock function will always return the response of "Your card application is under review"
- For the enquiry of failed transaction, the agent will prompt the user `transaction_id` and the user will have to input the format of `TX123`. The agent will keep prompting until the user gives the valid input. Once the user gives the valid input, the mock function replys with the reason of insufficient funds.
