import os
from typing import List


class Settings:
    def __init__(self) -> None:
        self.backend_port = int(os.getenv("COSTMELT_BACKEND_PORT", os.getenv("BACKEND_PORT", "8000")))
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.api_key = os.getenv("COSTMELT_API_KEY")
        self.cors_allow_origins = self._parse_cors_origins(
            os.getenv("COSTMELT_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        )

    def _parse_cors_origins(self, value: str) -> List[str]:
        if not value:
            return []
        parts = [item.strip() for item in value.split(",") if item.strip()]
        return parts


settings = Settings()
