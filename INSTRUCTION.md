# Проект qa-agents

Учебный проект интенсива «ИИ-агенты для QA». Здесь собираются локальные LLM-сервисы для задач тестирования: классификатор упавших автотестов, пакетная классификация и сборщик баг-репортов из описания в чате. Модель работает локально через Ollama.

Каждый следующий модуль курса **добавляет** код в этот проект по тем же правилам, новый проект не начинается.

---

## 1. Архитектура

### Слои

```
scripts/        точки запуска (аналог классов с main): только импортируют и вызывают
   │
services/       логика: собрать сообщения → вызвать клиент → проверить ответ
   │
   ├── prompts/     тексты для модели: системные инструкции и few-shot примеры
   ├── tools/       инструменты агента: описание для модели + функция Python
   ├── clients/     транспорт: HTTP-запросы к Ollama
   │
dto/            только данные и правила их проверки, без логики
errors.py       исключения проекта
config.py       настройки
```

**Правило зависимостей:** слой импортирует только то, что ниже него.

| Слой | Может импортировать | Не может |
|---|---|---|
| `dto`, `errors`, `config` | друг друга, сторонние библиотеки | `clients`, `services`, `prompts`, `scripts` |
| `prompts` | ничего из проекта | всё остальное |
| `clients` | `dto`, `errors`, `config` | `services`, `prompts`, `tools` |
| `tools` | `dto`, `config` | `clients`, `services`, `prompts` |
| `services` | `clients`, `dto`, `errors`, `prompts`, `tools`, `config` | `scripts` |
| `scripts` | всё | — |

Аналогия со Spring-проектом: `dto` ↔ DTO/entity, `clients` ↔ Feign/RestTemplate-клиенты, `services` ↔ `@Service`, `scripts` ↔ точки входа.

### Соглашения (обязательны для нового кода)

1. **Один класс — один файл.** Каждый DTO лежит в отдельном модуле: `chat_result.py` → `ChatResult`.
2. **DTO группируются по фиче в подпакеты:** `dto/ollama/`, `dto/bugReport/`, `dto/classificator/...`. В каждом подпакете есть `__init__.py`.
3. **Импорт всегда по полному пути до модуля:**
   ```python
   from qa_agents.dto.ollama.chat_result import ChatResult        # так
   from qa_agents.dto.ollama import ChatResult                    # не так: __init__.py пустой
   ```
4. **Скрипты ничего не объявляют**, кроме `main()` и функций вывода на экран. Логика живёт в `services`.
5. **Промпт фичи — отдельный файл в `prompts/`.** Его меняют чаще всего, и правка текста не должна трогать логику.
6. **Ответ модели всегда описывается Pydantic-DTO.** Из DTO строится JSON Schema для `format`, и тот же DTO проверяет ответ.

---

## 2. Структура проекта

```
qa-agents/
├── pyproject.toml                          зависимости и настройки (аналог pom.xml)
├── uv.lock                                 зафиксированные версии зависимостей
├── INSTRUCTION.md                          этот файл
├── data/
│   ├── sample_failures.json                8 учебных падений автотестов + ожидаемый класс
│   ├── bug_descriptions.json               3 описания бага «как в чате» + ожидаемые поля
│   └── test_history.json                   история 10 последних прогонов каждого учебного теста
├── src/qa_agents/
│   ├── config.py                           адрес Ollama, модели, таймауты, размер контекста
│   ├── errors.py                           OllamaUnavailableError, ClassificationError
│   ├── vram.py                             оценка: поместится ли модель в видеопамять
│   ├── clients/
│   │   └── ollama_client.py                OllamaClient: version, models, ps, chat
│   ├── dto/
│   │   ├── ollama/
│   │   │   ├── chat_result.py              ChatResult — ответ модели (текст или tool_calls) + токены + время
│   │   │   ├── tool_call.py                ToolCall — просьба модели вызвать инструмент
│   │   │   ├── model_info.py               ModelInfo — строка из `ollama list`
│   │   │   └── running_model.py            RunningModel — строка из `ollama ps`
│   │   ├── classificator/
│   │   │   ├── failureClassificator/
│   │   │   │   └── faulure_classificator.py    FailureClassification — класс одного падения
│   │   │   └── batchFailureClassificator/
│   │   │       ├── batch_item.py               Category, BatchItem — одно падение в пакете
│   │   │       └── batch_classification.py     BatchClassification — список BatchItem
│   │   ├── bugReport/
│   │   │   ├── environment.py              Environment — сторона, версия, стенд
│   │   │   └── bug_report.py               BugReport — баг-репорт (+ проверка нумерации шагов)
│   │   └── history/
│   │       └── test_run.py                 TestRun — один прогон теста в истории
│   ├── prompts/
│   │   ├── classifier_prompt.py            промпт и примеры классификатора падений
│   │   ├── bug_report_promt.py             промпт и примеры сборщика баг-репортов
│   │   └── tool_call_prompt.py             промпт аналитика с инструментами
│   ├── tools/
│   │   ├── test_history_tool.py            get_test_history: описание + реализация
│   │   └── registry.py                     TOOL_DEFINITIONS, execute_tool(call)
│   └── services/
│       ├── classifier.py                   classify_failure() — одно падение
│       ├── classifier_batch.py             classify_failure_list() — все падения одним запросом
│       ├── bug_report_extractor.py         build_report() — описание из чата → BugReport
│       └── single_tool_call.py             ask_with_tools() — один круг tool calling
├── scripts/
│   ├── check_ollama.py                     состояние Ollama: версия, модели, CPU/GPU
│   ├── vram_fit.py                         расчёт размера модели против реального
│   ├── raw_chat.py                         «сырой» POST /api/chat без клиента
│   ├── chat_demo.py                        опыты: роль system, история, temperature
│   ├── classify_failures.py                классификация 8 падений по одному
│   ├── classify_batch_failures.py          классификация 8 падений одним запросом
│   ├── classify_problems_and_bugs.py       баг-репорты по data/bug_descriptions.json
│   ├── bug_report_chat.py                  баг-репорт по описанию, введённому в консоли
│   └── tool_call_demo.py                   один вызов инструмента с печатью всей истории
└── tests/
    ├── test_dto_ollama.py                  разбор JSON Ollama в DTO
    ├── test_classifier.py                  классификатор с заглушкой вместо модели
    ├── test_tool_call.py                   tool calling: DTO, инструмент, реестр, один круг
    └── test_vram.py                        расчёт видеопамяти
```

---

## 3. Как устроен запрос к модели (общий для всех сервисов)

```
service.build_messages(text)
    system:    SYSTEM_PROMPT (+ JSON Schema текстом)
    user:      пример 1            ┐
    assistant: ответ на пример 1   │ few-shot из prompts/
    ...                            ┘
    user:      реальный текст
        │
        ▼
OllamaClient.chat(messages, response_format = Dto.model_json_schema())
    POST /api/chat  {model, messages, stream: false, think: false,
                     options: {temperature: 0, num_ctx}, format: <схема>}
        │
        ▼
ChatResult.content  →  Dto.model_validate_json(...)
    ok           → вернуть DTO
    ошибка       → повторить (до MAX_ATTEMPTS), затем ClassificationError
```

- **`format`** (JSON Schema) заставляет модель ответить JSON-ом нужной **формы**.
- **Pydantic** проверяет то, что форма не гарантирует: диапазоны чисел, правила валидаторов, оборванный ответ.
- **`evidence_found()`** — защита от галлюцинаций: цитата из ответа должна дословно найтись во входном тексте.

---

## 4. Настройки (`config.py`)

| Параметр | Значение | Зачем |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` (или переменная окружения) | в Docker адрес будет другим |
| `DEFAULT_MODEL` | `qwen3.5:4b` | основная модель: по замеру точнее 2b |
| `FAST_MODEL` | `qwen3.5:2b` | быстрая, менее точная |
| `REQUEST_TIMEOUT_SECONDS` | 10 | служебные запросы |
| `CHAT_TIMEOUT_SECONDS` | 180 | генерация на CPU/GPU медленная |
| `DEFAULT_NUM_CTX` | 4096 | окно контекста; лишнее Ollama **молча** обрезает |
| `GPU_VRAM_GB` | 4.0 | видеопамять GTX 1650 |

Следи за `result.input_tokens`: если он подбирается к `num_ctx`, начало промпта обрезается без ошибки.

---

## 5. Установка

```powershell
cd C:\dev\qa-agents
uv sync
```
`uv sync` создаёт `.venv`, ставит зависимости из `uv.lock` и устанавливает пакет `qa_agents` в режиме редактирования: правки в `src/` видны сразу.

**PyCharm:** интерпретатор — `.venv\Scripts\python.exe`, папка `src` → *Mark Directory as → Sources Root*.

**Ollama** должна быть запущена (иконка в трее), модели скачаны:
```powershell
ollama pull qwen3.5:4b
ollama pull qwen3.5:2b
```

---

## 6. Запуск

Все скрипты запускаются из корня проекта через `uv run`:

| Команда | Что делает | Время |
|---|---|---|
| `uv run python scripts/check_ollama.py` | версия Ollama, скачанные модели, модели в памяти | секунды |
| `uv run python scripts/vram_fit.py` | расчёт размера модели против реального, влезет ли в VRAM | секунды |
| `uv run python scripts/raw_chat.py` | печатает сырой запрос и ответ `/api/chat` | ~10 с |
| `uv run python scripts/chat_demo.py` | три опыта: system, история, temperature | 1–2 мин |
| `uv run python scripts/classify_failures.py` | 8 падений по одному, итог «верно X из 8» | 3–5 мин |
| `uv run python scripts/classify_batch_failures.py` | 8 падений одним запросом, проверка id | 1–3 мин |
| `uv run python scripts/classify_problems_and_bugs.py` | баг-репорты по `data/bug_descriptions.json` | 2–4 мин |
| `uv run python scripts/bug_report_chat.py` | интерактивно: описание бага → баг-репорт, выход `/bye` | ~1 мин на баг |
| `uv run python scripts/tool_call_demo.py` | вопрос → модель просит инструмент → результат → ответ | ~30 с |

Коды возврата: `0` — успех, `1` — Ollama недоступна или разбор не удался. Пригодится в CI.

---

## 7. Тесты и проверка стиля

```powershell
uv run pytest            # тесты (в Ollama не ходят)
uv run ruff check .      # линтер
uv run ruff format .     # автоформат
```

Тесты подменяют модель заглушкой `FakeClient`: у неё есть метод `chat`, и сервис не замечает подмены. Это позволяет проверять логику повторов и валидации без Ollama.

---

## 8. Как добавить новую фичу

На примере «сервис X»:

1. **DTO ответа модели** — `dto/<фича>/<имя>.py`, Pydantic `BaseModel`. Порядок полей: сначала факты и рассуждение, потом вывод. Если данных может не быть, поле `X | None`.
2. **Промпт** — `prompts/<фича>_prompt.py`: `SYSTEM_PROMPT` и `FEW_SHOT_EXAMPLES`. Ответы в примерах должны проходить валидацию твоего DTO, а сами примеры не должны совпадать с тестовыми данными.
3. **Сервис** — `services/<фича>.py`: `build_messages()` и основная функция. Возвращает DTO и бросает исключение из `errors.py`. Ничего не печатает.
4. **Данные** — `data/<фича>.json` с ожидаемым результатом, чтобы можно было посчитать «верно X из N».
5. **Инструменты (если нужны)** — `tools/<имя>_tool.py`: `DEFINITION` (JSON Schema для модели) и функция-реализация; регистрация в `tools/registry.py`. Ошибки инструмент не бросает, а возвращает текстом.
6. **Скрипт** — `scripts/<фича>.py`: прочитать данные, вызвать сервис, напечатать.
7. **Тест** — `tests/test_<фича>.py` с `FakeClient`.

---

## 9. Python ↔ Java: шпаргалка по конструкциям проекта

| Python | Java | Где встречается |
|---|---|---|
| папка с `__init__.py` | пакет | все подпакеты |
| `from a.b import C` | `import a.b.C;` | везде |
| `@dataclass` | Lombok `@Data` / `record` | `dto/ollama/*` |
| `class X(BaseModel)` | DTO + Jackson + Bean Validation | `dto/classificator`, `dto/bugReport` |
| `Field(ge=0, le=1)`, `Field(min_length=1)` | `@Min/@Max`, `@Size`, `@NotEmpty` | DTO |
| `Literal["a", "b"]` | `enum` | `Category`, `Priority`, `Stand` |
| `X \| None` | `@Nullable` / `Optional<X>` | необязательные поля |
| `@field_validator` | кастомный `ConstraintValidator` | `BugReport.steps` |
| `Model.model_json_schema()` | генерация JSON Schema из DTO | сервисы |
| `Model.model_validate_json(s)` | `readValue` + `validate` | сервисы |
| `@property` | вычисляемый геттер | `size_gb`, `gpu_percent` |
| `@staticmethod` | `static` метод | `from_api()` |
| `dict` / `list` / `set` / `tuple` | `Map` / `List` / `Set` / пара значений | везде |
| `try / except X as e / raise Y from e` | `try / catch / throw new Y(..., e)` | клиент, сервисы |
| `if __name__ == "__main__":` | `public static void main` | скрипты |
| `pytest.raises(X)` | `assertThrows(X.class, ...)` | тесты |
| `field(default_factory=list)` | поле с инициализатором `= new ArrayList<>()` | `ChatResult.tool_calls` |
| `function(**kwargs)` | вызов с аргументами из `Map` по именам | `tools/registry.py` |
