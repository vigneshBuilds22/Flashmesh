from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import logs, validation

s = get_settings()
app = FastAPI(title="FlashMesh API", version="0.1.0",
              description="AI runtime optimization layer: logs -> compact state -> grounded reasoning.")
app.add_middleware(CORSMiddleware, allow_origins=s.cors_list, allow_methods=["*"], allow_headers=["*"])
app.include_router(logs.router)
app.include_router(validation.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "mock_mode": s.mock_mode,
        "nebius_configured": bool(s.nebius_api_key),
        "tavily_configured": bool(s.tavily_api_key),
        "model": s.nebius_model,
    }
