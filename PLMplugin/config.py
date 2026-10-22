"""Единая конфигурация подключений PLMplugin.

Единственное место, откуда берутся хост/порты для API и WebSocket.
Порядок разрешения значений:
  1. ~/.local/share/robofactory-db/app/.env — порты AppImage-сборки
     (RF_API_PORT / RF_WS_PORT; AppRun пишет их при первом запуске)
  2. Дефолты dev-стека robofactory_db: localhost, api 8000, ws 8765

Хосты тоже можно переопределить через RF_API_HOST / RF_WS_HOST в том же .env.
"""

import os
from pathlib import Path

APP_ENV_PATH = Path.home() / ".local" / "share" / "robofactory-db" / "app" / ".env"

DEFAULT_API_HOST = "localhost"
DEFAULT_API_PORT = 8000
DEFAULT_WS_HOST = "localhost"
DEFAULT_WS_PORT = 8765


def _parse_env_file(path: Path) -> dict:
    """Читает простой KEY=VALUE .env файл. Без сторонних зависимостей."""
    result = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return result

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        result[key.strip()] = value.strip()

    return result


def _get_env_value(key: str) -> str:
    """Возвращает значение из .env AppImage-сборки или переменных окружения."""
    if APP_ENV_PATH.is_file():
        value = _parse_env_file(APP_ENV_PATH).get(key)
        if value:
            return value
    return os.environ.get(key, "")


def _resolve_port(key: str, default: int) -> int:
    value = _get_env_value(key)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_api_host() -> str:
    return _get_env_value("RF_API_HOST") or DEFAULT_API_HOST


def get_api_port() -> int:
    return _resolve_port("RF_API_PORT", DEFAULT_API_PORT)


def get_ws_host() -> str:
    return _get_env_value("RF_WS_HOST") or DEFAULT_WS_HOST


def get_ws_port() -> int:
    return _resolve_port("RF_WS_PORT", DEFAULT_WS_PORT)
