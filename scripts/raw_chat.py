"""Модуль 1.2: «сырой» запрос к модели — чистый requests, без нашего клиента.

Показывает, что запрос к LLM — это обычный POST с JSON, как в RestAssured.
Запуск: uv run python scripts/raw_chat.py
"""

import json

import requests

from qa_agents.config import CHAT_TIMEOUT_SECONDS, DEFAULT_MODEL, OLLAMA_BASE_URL

URL = OLLAMA_BASE_URL + "/api/chat"

# Тело запроса. Обычный словарь, requests сам превратит его в JSON.
payload = {
    "model": DEFAULT_MODEL,
    "messages": [
        {
            "role": "system",
            "content": "Ты помощник QA-инженера. Отвечай кратко, одним предложением.",
        },
        {
            "role": "user",
            "content": "Тест упал с java.net.ConnectException: Connection refused "
            "(localhost:8080). Что это за тип проблемы?",
        },
    ],
    "stream": False,
    "think": False,
    "options": {"temperature": 0},
}

# json.dumps — превратить словарь в красивую JSON-строку для печати.
# ensure_ascii=False — чтобы русские буквы печатались буквами, indent=2 — с отступами.
print("===== ЗАПРОС: POST", URL, "=====")
print(json.dumps(payload, ensure_ascii=False, indent=2))

response = requests.post(URL, json=payload, timeout=CHAT_TIMEOUT_SECONDS)
response.raise_for_status()
data = response.json()

print()
print("===== ОТВЕТ: статус", response.status_code, "=====")
print(json.dumps(data, ensure_ascii=False, indent=2))

print()
print("Текст ответа модели:", data["message"]["content"])
print("Токенов на входе:", data["prompt_eval_count"])
print("Токенов на выходе:", data["eval_count"])
print("Секунд всего:", round(data["total_duration"] / 1_000_000_000, 1))
