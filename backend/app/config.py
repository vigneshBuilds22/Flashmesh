from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    nebius_api_key: str = ""
    nebius_base_url: str = "https://api.tokenfactory.nebius.com/v1"
    nebius_model: str = "nvidia/Nemotron-3.5-Lightning"

    tavily_api_key: str = ""
    tavily_max_results: int = 5

    cors_origins: str = "http://localhost:3000"
    data_dir: str = "../data"
    max_upload_mb: int = 10
    extraction_chunk_tokens: int = 24000

    baseline_input_price_per_m: float = 0.60
    baseline_output_price_per_m: float = 1.80

    mock_mode: bool = False

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def uploads_dir(self) -> Path:
        p = Path(self.data_dir) / "uploads"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def results_dir(self) -> Path:
        p = Path(self.data_dir) / "results"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def samples_dir(self) -> Path:
        return Path(self.data_dir) / "sample_logs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
