# FlashMesh

AI runtime optimization layer for agentic systems: compress noisy infrastructure logs into a compact
machine-readable state, ground it with web search, then reason over the state instead of the raw logs.

**Status:** backend and frontend complete (MVP).

## Structure
```
flashmesh/
├── backend/   FastAPI service (Python 3.11)
├── frontend/  Next.js 15 + TypeScript + Tailwind + shadcn/ui dashboard
├── data/      sample logs + generator, runtime uploads/results
├── docs/      ARCHITECTURE.md
└── README.md
```

## Run the backend locally
```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add NEBIUS_API_KEY and TAVILY_API_KEY, or set MOCK_MODE=true
uvicorn app.main:app --reload --port 8000
```
Docs: http://localhost:8000/docs

```bash
curl -X POST localhost:8000/api/samples/k8s_redis_oom.log          # -> upload_id
curl -X POST localhost:8000/api/analyze/<upload_id> | jq .metrics
```
Regenerate the ~28k-token demo log: `python data/generate_sample_log.py` (run from `data/`).

## Run the frontend locally
Requires Node 20+. Start the backend first.
```bash
cd frontend
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev                  # http://localhost:3000
```
Click "Analyze the demo incident" on the homepage, or drop in your own `.log` file.
On Windows PowerShell use `copy .env.example .env.local`.

## Pages
- `/` title, before/after compression visual, upload area, pipeline workflow
- `/analysis/[id]` log preview and token count, state graph JSON, dependency chain, Tavily grounding, root cause + remediation + fix + confidence, metrics dashboard with per-stage latency

Results are cached by id on the backend, so refreshing an analysis page does not re-bill the model.

## Validation agent (does the compact state preserve enough to act on?)
Four simulated tools (`restart_service`, `increase_memory_limit`, `rollback_release`, `scale_deployment`);
the agent reads the real FlashMesh state and must pick the right one for three incident types.
```bash
cd data && python generate_validation_logs.py     # creates 2 synthetic logs; swap in real incident logs of the same names
cd ../backend
python -m scripts.validate_agent --baseline      # --baseline also runs the agent on the raw logs as a control
```
Needs real Nebius credentials (`MOCK_MODE=false`). Prints a table and writes `data/validation/report.json`.
Tool arguments are range-checked; malformed or out-of-range calls count as failures.

## Environment variables
See `backend/.env.example`. Set `NEBIUS_MODEL` to the exact Nemotron model ID shown in your Nebius Token Factory catalog.

## Deploy (backend)
```bash
docker build -t flashmesh-api backend
docker run -p 8000:8000 --env-file backend/.env -v $PWD/data:/data flashmesh-api
```
Works on any container host (Fly.io, Render, Cloud Run). Set `CORS_ORIGINS` to your frontend URL.

## Deploy (frontend)
Deploy `frontend/` to Vercel (set root directory to `frontend`) and add the env var
`NEXT_PUBLIC_API_URL=https://<your-backend-host>`. Then set the backend's `CORS_ORIGINS` to the Vercel URL.
Self-host alternative: `npm run build && npm start`.
