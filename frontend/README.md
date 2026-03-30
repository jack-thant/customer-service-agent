# Service AI Frontend

Next.js frontend for **Service AI**. This app provides:

- Customer support chat UI
- Knowledge base configuration and re-ingestion trigger
- Mistake review and status updates
- Agent workflow UI (upload docs, build specs, activate versions, chat with active spec)

## Tech Stack

- Next.js 16 (App Router)
- React 19
- TypeScript
- Tailwind CSS 4
- shadcn-style UI primitives

## Prerequisites

- Node.js 20+
- npm 10+
- A running backend API (default: `http://localhost:8000`)

## Environment Variables

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

If omitted, the frontend falls back to `http://localhost:8000`.

## Install and Run

From `frontend/`:

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Available Scripts

From `frontend/`:

```bash
npm run dev
npm run build
npm run start
npm run lint
```

## Pages

- `/` - Customer support chat
- `/config` - Knowledge base URL + additional guidelines + re-ingestion
- `/mistakes` - Mistake queue and lifecycle management
- `/agent` - Agent document upload, build pipeline, spec activation, runtime chat

## API Integration

All API calls are defined in `lib/api.ts` and target `NEXT_PUBLIC_API_URL`.

Core backend routes used by the UI:

- `GET /` health/info check
- `POST /chat`
- `GET /config`
- `PUT /config`
- `POST /config/reingest`
- `GET /mistakes`
- `POST /mistakes`
- `PATCH /mistakes/{mistake_id}`
- `POST /agent/docs`
- `POST /agent/build`
- `GET /agent/build/{job_id}`
- `POST /agent/meta-chat`
- `GET /agent/spec/active`
- `GET /agent/specs`
- `POST /agent/spec/{version}/activate`
- `POST /agent/chat`

## Project Structure

```text
frontend/
  app/                 # App Router pages
  components/          # Shared UI and feature components
  lib/
    api.ts             # Backend API client
    types.ts           # Shared frontend types
```

## Notes

- The frontend assumes CORS is enabled on the backend.
- Re-ingestion is triggered from `/config` and executed by the backend pipeline.
- The deployment for frontend is via Vercel.
