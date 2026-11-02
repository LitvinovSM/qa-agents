"""Все настройки проекта в одном месте (аналог application.properties).

Остальные файлы берут значения отсюда: поменял здесь — поменялось везде.
"""

import os

# Адрес Ollama. Берётся из переменной окружения, чтобы в Docker (День 7) не менять код.
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Основная модель агентов: по замеру 4b отвечает правильно, 2b — быстрее, но ошибается.
DEFAULT_MODEL: str = "qwen3.5:4b"
FAST_MODEL: str = "qwen3.5:2b"

# Таймаут служебных HTTP-запросов, секунды.
REQUEST_TIMEOUT_SECONDS: int = 10

# Объём видеопамяти GTX 1650 — для задания про VRAM.
GPU_VRAM_GB: float = 4.0
