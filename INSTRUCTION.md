# Проект qa-agents — пошаговая инструкция

Это база для всего курса. Каждый следующий модуль будет **добавлять** файлы в этот же проект, а не начинать новый.

В коде у каждого класса и метода короткий комментарий: зачем он нужен. Эта инструкция объясняет, **зачем** нужен каждый файл и **какие новые конструкции Python** в нём встречаются — держи её открытой рядом с кодом.

---

## Что получится

```
qa-agents/
├── pyproject.toml              ← настройки проекта и зависимости (аналог pom.xml)
├── .gitignore                  ← что не попадает в git
├── INSTRUCTION.md              ← этот файл
├── src/
│   └── qa_agents/              ← НАШ ПАКЕТ (общий код, его импортируют скрипты)
│       ├── __init__.py         ← делает папку пакетом
│       ├── config.py           ← все настройки в одном месте
│       ├── errors.py           ← все исключения проекта
│       ├── dto/                ← только данные (DTO), без логики
│       │   ├── ollama.py           ModelInfo, RunningModel, ChatResult
│       │   └── classification.py   FailureClassification (Pydantic)
│       ├── clients/            ← HTTP-клиенты внешних систем
│       │   └── ollama_client.py    OllamaClient
│       ├── prompts/            ← тексты промптов и few-shot примеры
│       │   └── classifier_prompt.py
│       ├── services/           ← логика: клиент + DTO + промпт
│       │   └── classifier.py       classify_failure()
│       └── vram.py             ← ЗАДАНИЕ 2: две функции пишешь ты
├── data/
│   └── sample_failures.json    ← учебные падения с ожидаемым классом
├── scripts/                    ← точки запуска: только импортируют и вызывают
│   ├── check_ollama.py
│   ├── vram_fit.py
│   ├── raw_chat.py
│   ├── chat_demo.py
│   └── classify_failures.py
└── tests/                      ← тесты pytest
    ├── test_dto_ollama.py      ← тесты DTO Ollama
    ├── test_classifier.py      ← тесты классификатора (с заглушкой вместо модели)
    └── test_vram.py            ← тесты к заданию 2
```

Слои как в Spring-проекте: `dto` → `clients` → `services` → `scripts`. Каждый слой импортирует только нижние, а `scripts` — это `main`-классы, которые ничего не объявляют, только вызывают.

**Аналогия с Maven-проектом:**

| Python (наш проект) | Java / Maven |
|---|---|
| `pyproject.toml` | `pom.xml` |
| `src/qa_agents/` | `src/main/java/ru/qa/agents/` |
| `tests/` | `src/test/java/` |
| `uv sync` | `mvn install` (скачать зависимости и собрать) |
| `uv run pytest` | `mvn test` |
| `.venv/` | локальный `~/.m2` + JDK, но **свой для каждого проекта** |

**Почему код разделён на `src/qa_agents` и `scripts`.** В пакете лежит **переиспользуемый** код: клиент, настройки. Его будут импортировать все будущие агенты. В `scripts/` лежат **точки запуска**, как классы с `main` в Java. Так агент Дня 2 возьмёт тот же `OllamaClient`, а не скопирует его.

---

## Шаг 1. Распаковать проект

1. Скачай архив `qa-agents.zip` и распакуй его, например, в `C:\Users\DELL\projects\`. Должна появиться папка `C:\Users\DELL\projects\qa-agents`.
2. Открой PowerShell и перейди в папку проекта:

   ```powershell
   cd C:\Users\DELL\projects\qa-agents
   ```

**Как проверить:** команда `dir` показывает `pyproject.toml`, `src`, `scripts`, `tests`.

---

## Шаг 2. Файл `pyproject.toml` — настройки проекта

**Где:** корень проекта.
**Что делает:** описывает проект и его зависимости.

Секции файла:

| Секция | Что значит | Аналог в Maven |
|---|---|---|
| `[project]` | имя, версия, минимальный Python, **рабочие** зависимости (`requests`) | `<artifactId>`, `<version>`, `<dependencies>` |
| `[dependency-groups] dev` | зависимости **только для разработки**: `pytest`, `ruff` | `<scope>test</scope>` |
| `[build-system]` | чем «собрать» наш пакет (`hatchling`) | `maven-compiler-plugin` |
| `[tool.hatch...]` | где лежит код пакета (`src/qa_agents`) | `<sourceDirectory>` |
| `[tool.pytest...]` | где искать тесты | настройки `surefire` |
| `[tool.ruff]` | правила линтера | настройки Checkstyle |

**Зачем нужен `[build-system]`.** Без него скрипт из `scripts/` не сможет сделать `import qa_agents`: Python не знает, где искать пакет. Секция говорит uv: «установи папку `src/qa_agents` в виртуальное окружение как библиотеку». После этого импорт работает из любого файла проекта, как зависимость из `~/.m2` у Maven.

---

## Шаг 3. Установить зависимости

```powershell
uv sync
```

Что происходит:
1. uv читает `pyproject.toml`.
2. Создаёт виртуальное окружение `.venv` (отдельный Python только для этого проекта).
3. Скачивает `requests`, `pytest`, `ruff` и всё, от чего они зависят.
4. Устанавливает **наш пакет** `qa_agents` в «редактируемом» режиме: правишь код в `src/`, и изменения видны сразу, без переустановки.
5. Записывает точные версии в `uv.lock`, это «замороженный» список версий, аналог зафиксированных версий в `pom.xml`. Этот файл коммитят в git.

**Как проверить:** в конце вывода нет слова `error`, а в папке появились `.venv` и `uv.lock`.

**Если ошибка:**
- `uv : Имя "uv" не распознано` — uv не в PATH. Закрой и открой PowerShell заново. Если не помогло, переустанови uv по официальной инструкции: https://docs.astral.sh/uv/getting-started/installation/
- `No interpreter found for Python >=3.11` — у тебя Python старше 3.11. Выполни `uv python install 3.12`, затем снова `uv sync`.
- Ошибки сети или SSL — проверь, не включён ли VPN или прокси, который ломает HTTPS, и повтори.

---

## Шаг 4. Открыть проект в PyCharm

1. **File → Open →** папка `qa-agents`.
2. PyCharm обычно сам находит `.venv`. Проверь внизу справа: должно быть написано что-то вроде `Python 3.12 (qa-agents)`.
3. Если интерпретатор не подхватился: **Settings → Project: qa-agents → Python Interpreter → Add Interpreter → Add Local Interpreter → Select existing →** укажи `qa-agents\.venv\Scripts\python.exe`.
4. Пометь папку `src` как источник кода: правый клик по `src` → **Mark Directory as → Sources Root**. Тогда PyCharm не будет подчёркивать `import qa_agents` красным.

---

## Шаг 5. Файл `src/qa_agents/__init__.py`

**Что делает:** превращает папку `qa_agents` в **пакет** Python.

**Новое понятие — пакет (package).** Папка с файлом `__init__.py`. Каждый `.py`-файл внутри называется **модулем (module)**.

| Python | Java |
|---|---|
| пакет `qa_agents` (папка с `__init__.py`) | пакет `ru.qa.agents` |
| модуль `clients/ollama_client.py` (файл) | класс-файл, но в одном модуле может быть **несколько** классов и функций |
| `from qa_agents.config import DEFAULT_MODEL` | `import static ru.qa.agents.Config.DEFAULT_MODEL;` |

Внутри файла только описание пакета (docstring). Код там не нужен.

---

## Шаг 6. Файл `src/qa_agents/config.py` — настройки

**Что делает:** хранит все настройки в одном месте: адрес Ollama, имена моделей, таймаут, объём видеопамяти.

**Новые конструкции:**

| Конструкция | Что значит | Аналог Java |
|---|---|---|
| `import os` | подключить стандартный модуль | `import java.lang.System;` |
| `os.getenv("ИМЯ", "умолчание")` | прочитать переменную окружения, а если её нет — взять значение по умолчанию | `System.getenv().getOrDefault(...)` |
| `OLLAMA_BASE_URL: str = ...` | переменная с **подсказкой типа** `str`. Python тип **не проверяет**, это подсказка для тебя, IDE и mypy | `String OLLAMA_BASE_URL = ...` |
| `ИМЯ_ЗАГЛАВНЫМИ` | соглашение «это константа». Слова `final` в Python нет | `static final` |
| `str`, `int`, `float` | строка, целое число, дробное число | `String`, `int`, `double` |

**Почему `DEFAULT_MODEL = "qwen3.5:4b"`.** По твоему замеру 4b ответила правильно 3 из 3, а 2b ошиблась 3 из 3.

**Почему адрес Ollama берётся из переменной окружения.** На Дне 7 агент будет работать в Docker-контейнере, и там адрес станет другим. Поменяем переменную окружения, код трогать не придётся.

---

## Шаг 7. Клиент к Ollama: `dto/ollama.py`, `errors.py`, `clients/ollama_client.py`

**Что делает:** обёртка над HTTP API Ollama, как твой класс-обёртка над RestAssured во фреймворке автотестов. Скрипты не пишут HTTP-запросы сами, они зовут `client.list_models()`.

Классы и где они лежат:

| Класс | Файл | Роль | Аналог Java |
|---|---|---|---|
| `OllamaUnavailableError` | `errors.py` | своё исключение «Ollama недоступна» | `class OllamaUnavailableException extends RuntimeException` |
| `ModelInfo` | `dto/ollama.py` | DTO «скачанная модель» (строка из `ollama list`) | DTO с Lombok `@Data` |
| `RunningModel` | `dto/ollama.py` | DTO «модель в памяти» (строка из `ollama ps`) | DTO с Lombok `@Data` |
| `ChatResult` | `dto/ollama.py` | DTO ответа модели | DTO с Lombok `@Data` |
| `OllamaClient` | `clients/ollama_client.py` | клиент с методами-запросами | класс-клиент |

Методы клиента:

| Метод | HTTP-запрос | Что возвращает |
|---|---|---|
| `get_version()` | `GET /api/version` | строку с версией |
| `list_models()` | `GET /api/tags` | `list[ModelInfo]` |
| `list_running_models()` | `GET /api/ps` | `list[RunningModel]` |

**Новые конструкции (по порядку появления в файле):**

1. **`from X import Y`** — взять из модуля `X` только объект `Y`.

2. **Наследование:** `class OllamaUnavailableError(Exception):`. Родитель пишется в скобках вместо `extends`. `pass` значит «тело пустое»: пустые `{}` в Python не бывают.

3. **`@dataclass`** — **декоратор**. Строка с `@` над классом «дописывает» в него код. Ты объявляешь только поля (`name: str`), а конструктор, `toString` (в Python `__repr__`) и `equals` (`__eq__`) появляются автоматически. **Это прямой аналог Lombok `@Data` или Java `record`.**
   ```python
   model = ModelInfo(
       name="qwen3.5:4b", size_bytes=3400000000, parameter_size="4.7B", quantization="Q4_K_M"
   )
   # Java: new ModelInfo("qwen3.5:4b", 3400000000L, "4.7B", "Q4_K_M");  — слова new в Python нет
   ```

4. **`self`** — ссылка на текущий объект, аналог `this`. В Python её **обязательно** пишут первым параметром у каждого метода объекта, но при вызове не передают: `model.size_gb`, а не `model.size_gb(model)`.

5. **`@property`** — метод становится «вычисляемым полем». Пишешь `model.size_gb` **без скобок**, а внутри выполняется расчёт. Аналог геттера `getSizeGb()`, который считает значение на лету.

6. **`@staticmethod`** — метод без `self`, аналог `public static`. У нас это **фабричный метод** `from_api(data)`: превращает кусок JSON в DTO. Это ручная версия того, что Jackson делает при десериализации.

7. **`dict` (словарь)** — пары «ключ → значение», аналог `Map<String, Object>`. Метод `requests` `.json()` возвращает именно словари и списки.
   - `data["name"]` — достать значение; если ключа нет, будет **ошибка** `KeyError`.
   - `data.get("name", "unknown")` — достать значение; если ключа нет, вернётся `"unknown"`. Аналог `map.getOrDefault(...)`. Мы везде используем `.get`, чтобы не упасть, если Ollama поменяет формат ответа.

8. **`list[ModelInfo]`** — подсказка типа «список объектов ModelInfo», аналог `List<ModelInfo>`.
   - `result = []` — пустой список (`new ArrayList<>()`).
   - `result.append(x)` — добавить элемент (`list.add(x)`).
   - `for item in список:` — цикл по элементам (`for (Item item : list)`).

9. **`__init__`** — **конструктор**. Параметры со значениями по умолчанию (`base_url: str = OLLAMA_BASE_URL`) позволяют вызвать `OllamaClient()` без аргументов. В Java для этого понадобилась бы перегрузка конструктора.

10. **`_get`** — подчёркивание в начале имени означает «внутренний метод, снаружи не вызывай». Аналог `private`, но Python вызов не запрещает, это только соглашение.

11. **f-строка:** `f"{self.base_url}{path}"` подставляет значения в строку. Аналог `String.format` или конкатенации.

12. **`try / except / raise ... from e`** — аналог `try / catch / throw new X("...", e)`:
    ```python
    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.ConnectionError as e:  # catch (ConnectException e)
        raise OllamaUnavailableError("...") from e  # throw new ...Exception("...", e)
    ```
    `from e` сохраняет исходную ошибку как **причину**, это как `cause` в Java.

13. **`requests`:**
    - `requests.get(url, timeout=10)` — GET-запрос, аналог `given().when().get(url)`. **Всегда указывай `timeout`**, иначе запрос может висеть вечно.
    - `response.raise_for_status()` — бросить исключение при статусе 4xx/5xx.
    - `response.json()` — разобрать тело ответа в словари и списки.

---

## Шаг 8. Файл `scripts/check_ollama.py` — задание 1

**Что делает:** печатает версию Ollama, скачанные модели и модели в памяти с процентом на GPU. Это твои `ollama list` + `ollama ps`, но через HTTP API из Python. Если Ollama не запущена, выводит понятное сообщение и возвращает код `1`.

**Новые конструкции:**

| Конструкция | Что значит | Аналог Java |
|---|---|---|
| `def main() -> int:` | функция, возвращает целое число | `static int main()` |
| `print(...)` | вывод в консоль | `System.out.println(...)` |
| `len(models)` | длина списка | `models.size()` |
| `if not models:` | «если список пустой»: пустой список считается «ложью» | `if (models.isEmpty())` |
| `f"{x:.1f}"` | число с 1 знаком после запятой | `String.format("%.1f", x)` |
| `f"{name:<15}"` | выровнять влево в поле 15 символов | `String.format("%-15s", name)` |
| `if __name__ == "__main__":` | «этот код выполняется, только когда файл запущен напрямую» | `public static void main(String[] args)` |
| `sys.exit(main())` | завершить программу с кодом возврата | `System.exit(main())` |

**Почему важен код возврата 0/1.** На Дне 7 Jenkins будет запускать проверки, и шаг пайплайна упадёт, если программа вернёт не `0`. Это та же логика, что у `mvn test`.

### Запуск

1. Убедись, что Ollama запущена (иконка ламы в трее).
2. Чтобы увидеть модель «в памяти», в **отдельном** окне PowerShell выполни `ollama run qwen3.5:4b`, задай любой вопрос и не закрывай окно.
3. В окне проекта выполни:
   ```powershell
   uv run python scripts/check_ollama.py
   ```
   `uv run` запускает команду **внутри виртуального окружения проекта**, активировать `.venv` вручную не нужно.

**Ожидаемый результат** (цифры у тебя будут свои):
```
Ollama работает, версия: 0.xx.x

Скачано моделей: 2
  qwen3.5:4b        3.4 ГБ  параметров: 4.7B   квантизация: Q4_K_M
  qwen3.5:2b        2.7 ГБ  параметров: 2.3B   квантизация: Q4_K_M

Загружено в память сейчас: 1
  qwen3.5:4b        3.7 ГБ  CPU/GPU: 50%/50%  контекст: 4096
```

**Проверь обработку ошибки (это и есть суть задания 1):** закрой Ollama (правый клик по иконке в трее → Quit) и запусти скрипт снова. Должна появиться строка `[ОШИБКА] Ollama не отвечает...`, а **не** длинный стектрейс. Потом запусти Ollama обратно.

**Если ошибка:**
- `ModuleNotFoundError: No module named 'qa_agents'` — запускаешь не через `uv run` или не выполнил `uv sync`. Выполни `uv sync` в корне проекта и запускай строго `uv run python scripts/...`.
- `ModuleNotFoundError: No module named 'requests'` — та же причина.
- Кракозябры вместо русских букв — выполни в PowerShell `$env:PYTHONUTF8=1` и запусти снова.

---

## Шаг 9. Файлы тестов `tests/`

### `tests/test_dto_ollama.py` — тесты DTO

Проверяют, что JSON правильно превращается в `ModelInfo` и `RunningModel`. **В Ollama не ходят**, поэтому проходят без неё. Это аналог юнит-теста десериализации через Jackson.

**Как pytest находит тесты (отличие от JUnit):**
- файл называется `test_*.py`;
- функция называется `test_*`;
- аннотация `@Test` **не нужна**;
- проверка — обычный `assert условие` вместо `assertEquals`.

### `tests/test_vram.py` — тесты к заданию 2

Пять тестов на функции `estimate_gb` и `fits`, включая граничное значение (ровно 4.0 ГБ). `pytest.approx(2.25)` — сравнение дробных чисел с допуском, аналог `assertEquals(2.25, actual, 0.001)`.

### Запуск

```powershell
uv run pytest
```

**Ожидаемый результат сейчас:** `5 failed, 4 passed`. Падают **только** тесты `test_vram.py` с ошибкой `NotImplementedError`. Так и задумано: это красная фаза TDD, функции ты ещё не написал.

---

## Шаг 10. Файл `src/qa_agents/vram.py` — задание 2 (пишешь ты)

**Что делает:** две функции-заготовки. Сейчас они бросают `NotImplementedError`, аналог `throw new UnsupportedOperationException("TODO")`.

**Новое понятие — функция вне класса.** `def estimate_gb(...)` — обычная функция, не метод. В Java так нельзя, там всё внутри классов; ближайший аналог — `public static` метод в утилитном классе.

**Твоя задача:**
1. В `estimate_gb` замени строку `raise NotImplementedError(...)` на `return <формула>`. Формула и подсказка есть в комментарии функции.
2. В `fits` замени строку `raise NotImplementedError(...)` на `return <условие>`. Сравнение (`<=`) само по себе даёт `True`/`False`, его можно сразу вернуть.
3. Запусти `uv run pytest`. Цель: `9 passed`.
4. Запусти `uv run python scripts/vram_fit.py`. Скрипт напечатает таблицу «расчёт / реальный размер / влезет ли».
5. В конце `scripts/vram_fit.py` есть `TODO`: одной строкой комментария объясни, почему реальный размер qwen3.5 больше расчётного (подсказка была в Модуле 1.1).

**Новое в `vram_fit.py`:**

| Конструкция | Что значит | Аналог Java |
|---|---|---|
| `{"qwen3.5:2b": 2.0, ...}` | создать словарь | `Map.of("qwen3.5:2b", 2.0, ...)` |
| `словарь[ключ] = значение` | положить пару | `map.put(key, value)` |
| `ключ in словарь` | есть ли такой ключ | `map.containsKey(key)` |
| `for name, params in d.items():` | перебрать пары ключ–значение | `for (var e : map.entrySet())` |
| `"да" if условие else "нет"` | тернарный оператор | `условие ? "да" : "нет"` |

---

## Шаг 11. Проверить стиль кода

```powershell
uv run ruff check .
uv run ruff format .
```

`ruff check` ищет ошибки и плохие практики (как Checkstyle). `ruff format` форматирует код автоматически (как Ctrl+Alt+L в IDEA).

---

## Чекпоинт

- [ ] `uv sync` прошёл без ошибок, появились `.venv` и `uv.lock`.
- [ ] PyCharm видит интерпретатор `.venv`.
- [ ] `uv run python scripts/check_ollama.py` выводит версию и модели.
- [ ] При выключенной Ollama скрипт выводит `[ОШИБКА] ...`, а не стектрейс.
- [ ] Ты дописал `vram.py`, и `uv run pytest` показывает `9 passed`.
- [ ] `uv run python scripts/vram_fit.py` печатает таблицу, а в `TODO` записано объяснение.

Что прислать наставнику: вывод `check_ollama.py`, вывод `uv run pytest` и твой код двух функций из `vram.py` вместе с ответом из `TODO`.
