import os

from config import Settings


def test_settings_use_safe_defaults(monkeypatch):
    monkeypatch.delenv("COSTMELT_BACKEND_PORT", raising=False)
    monkeypatch.delenv("COSTMELT_CORS_ORIGINS", raising=False)
    monkeypatch.delenv("COSTMELT_API_KEY", raising=False)

    settings = Settings()

    assert settings.backend_port == 8000
    assert settings.cors_allow_origins == ["http://localhost:3000", "http://127.0.0.1:3000"]
    assert settings.api_key is None


def test_settings_parse_cors_from_env(monkeypatch):
    monkeypatch.setenv("COSTMELT_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")

    settings = Settings()

    assert settings.cors_allow_origins == ["http://localhost:3000", "http://127.0.0.1:3000"]
