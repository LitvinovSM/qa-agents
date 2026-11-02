"""HTTP-клиент для служебного API Ollama.

Что умеет класс OllamaClient:
    get_version()          -> версия сервера Ollama        (GET /api/version)
    list_models()          -> скачанные модели, как `ollama list` (GET /api/tags)
    list_running_models()  -> модели в памяти, как `ollama ps`    (GET /api/ps)

Аналогия с Java: это как твой класс-обёртка над RestAssured в фреймворке
автотестов — тесты не пишут given().when().get(...) сами, а зовут
client.getUsers(). Здесь то же самое, только для LLM-сервера.

В Модуле 1.2 мы добавим сюда метод chat() — запрос к самой модели.
"""

# --- Импорты ------------------------------------------------------------------
# `from X import Y` — взять из модуля X только объект Y.
# Аналог Java: `import java.util.List;`.

# dataclass — «декоратор», который сам генерирует конструктор, toString, equals.
# Аналог Lombok @Data / Java record. Подробнее — ниже у класса ModelInfo.
from dataclasses import dataclass

# requests — сторонняя библиотека для HTTP-запросов (мы указали её в pyproject.toml).
import requests

# Берём настройки из нашего config.py.
# `qa_agents.config` — это файл src/qa_agents/config.py.
from qa_agents.config import OLLAMA_BASE_URL, REQUEST_TIMEOUT_SECONDS

# Сколько байт в одном гигабайте. Ollama отдаёт размеры в байтах.
# 1024 ** 3 — это 1024 в третьей степени (оператор ** — возведение в степень).
BYTES_IN_GB = 1024**3


# =============================================================================
# Своё исключение (exception).
#
# `class OllamaUnavailableError(Exception):` — объявляем класс-наследник Exception.
# Аналог Java: `public class OllamaUnavailableException extends RuntimeException {}`.
# В скобках после имени класса пишется РОДИТЕЛЬ (вместо слова extends).
#
# Зачем своё исключение: чтобы скрипт мог поймать ОДНУ понятную ошибку
# «Ollama недоступна», а не разбираться с десятком видов ошибок requests.
#
# `pass` — «тело пустое, ничего не делаем». В Python нельзя оставить {} пустыми,
# поэтому пишут pass.
# =============================================================================
class OllamaUnavailableError(Exception):
    pass


# =============================================================================
# DTO «скачанная модель» — одна строка из `ollama list`.
#
# @dataclass — ДЕКОРАТОР: строка с @ над классом, которая «дописывает» в класс код.
# Аналог Lombok-аннотации @Data над Java-классом: ты объявляешь только поля,
# а конструктор, toString и equals появляются сами.
#
# Поля объявляются как `имя: тип`. Это и есть поля DTO,
# как `private String name;` в Java.
#
# Создать объект: ModelInfo(name="qwen3.5:4b", size_bytes=3400000000, ...)
# Аналог Java: new ModelInfo("qwen3.5:4b", 3400000000L, ...).
# В Python слово `new` не пишется.
# =============================================================================
@dataclass
class ModelInfo:
    name: str  # имя с тегом, например "qwen3.5:4b"
    size_bytes: int  # размер файла модели в байтах
    parameter_size: str  # сколько параметров, например "4.7B" (строкой, как отдаёт Ollama)
    quantization: str  # уровень квантизации, например "Q4_K_M"

    # @property превращает метод в «вычисляемое поле»:
    # пишешь model.size_gb БЕЗ скобок, а внутри выполняется этот метод.
    # Аналог Java: геттер getSizeGb(), который считает значение на лету.
    #
    # `self` — ссылка на текущий объект. Аналог `this` в Java.
    # В Python её ОБЯЗАТЕЛЬНО писать первым параметром у методов объекта.
    #
    # `-> float` — подсказка типа возвращаемого значения (как `float` перед
    # именем метода в Java).
    @property
    def size_gb(self) -> float:
        return self.size_bytes / BYTES_IN_GB

    # @staticmethod — метод, которому не нужен объект (нет self).
    # Аналог Java: `public static ModelInfo fromApi(Map<String, Object> data)`.
    # Это «фабричный метод»: превращает кусок JSON-ответа (словарь) в наш DTO.
    # Похоже на то, что делает Jackson при десериализации, только вручную.
    #
    # `dict` — СЛОВАРЬ: набор пар ключ → значение. Аналог Java Map<String, Object>.
    # Ответ requests .json() возвращает именно словари и списки.
    @staticmethod
    def from_api(data: dict) -> "ModelInfo":
        # data.get("ключ", значение_по_умолчанию) — достать значение по ключу.
        # Если ключа нет — вернётся значение по умолчанию, а не ошибка.
        # Аналог Java: map.getOrDefault("details", Map.of()).
        # Пишем .get, а не data["details"], чтобы не упасть, если поля нет
        # (API Ollama иногда меняется — защищаемся).
        details = data.get("details", {})
        return ModelInfo(
            name=data.get("name", "unknown"),
            size_bytes=data.get("size", 0),
            parameter_size=details.get("parameter_size", "?"),
            quantization=details.get("quantization_level", "?"),
        )


# =============================================================================
# DTO «модель, загруженная в память» — одна строка из `ollama ps`.
# Здесь есть size_vram — сколько байт модели лежит в ВИДЕОпамяти.
# Из этого считаем ту самую колонку PROCESSOR (сколько % на GPU).
# =============================================================================
@dataclass
class RunningModel:
    name: str
    size_bytes: int  # сколько всего памяти занимает модель (VRAM + RAM)
    size_vram_bytes: int  # из них — в видеопамяти
    context_length: int  # размер контекстного окна (колонка CONTEXT в `ollama ps`)

    @property
    def size_gb(self) -> float:
        return self.size_bytes / BYTES_IN_GB

    @property
    def gpu_percent(self) -> float:
        # Защита от деления на ноль: если размер 0 — сразу возвращаем 0.
        # В Python `if` без скобок и с двоеточием в конце; тело — с отступом.
        if self.size_bytes == 0:
            return 0.0
        return self.size_vram_bytes / self.size_bytes * 100

    @staticmethod
    def from_api(data: dict) -> "RunningModel":
        return RunningModel(
            name=data.get("name", "unknown"),
            size_bytes=data.get("size", 0),
            size_vram_bytes=data.get("size_vram", 0),
            context_length=data.get("context_length", 0),
        )


# =============================================================================
# Сам клиент.
#
# `class OllamaClient:` — обычный класс (без родителя).
# =============================================================================
class OllamaClient:
    # __init__ — КОНСТРУКТОР. Вызывается при OllamaClient(...).
    # Аналог Java: public OllamaClient(String baseUrl, int timeoutSeconds) {...}
    #
    # `base_url: str = OLLAMA_BASE_URL` — параметр со значением по умолчанию.
    # Можно вызвать OllamaClient() без аргументов — возьмётся адрес из config.py.
    # В Java для этого пришлось бы писать второй конструктор (перегрузку).
    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        # self.поле = значение — создаём поле объекта.
        # Аналог Java: this.baseUrl = baseUrl;
        # .rstrip("/") убирает слеш в конце адреса, чтобы не получилось "//api".
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    # ------------------------------------------------------------------------
    # Приватный вспомогательный метод.
    # Имя с подчёркиванием `_get` — договорённость «это для внутреннего
    # использования». Аналог private в Java (но Python его не запрещает, это соглашение).
    #
    # Делает GET-запрос и возвращает разобранный JSON (словарь).
    # Все ошибки сети превращает в нашу OllamaUnavailableError.
    # ------------------------------------------------------------------------
    def _get(self, path: str) -> dict:
        # f-строка: f"...{переменная}..." подставляет значение внутрь строки.
        # Аналог Java: String.format("%s%s", baseUrl, path) или baseUrl + path.
        url = f"{self.base_url}{path}"

        # try/except — аналог try/catch в Java.
        try:
            # requests.get(url, timeout=...) — отправить GET-запрос.
            # Аналог RestAssured: given().when().get(url).
            # `timeout=` — ИМЕНОВАННЫЙ аргумент: передаём значение по имени параметра.
            # Без timeout запрос может висеть вечно — всегда ставь timeout.
            response = requests.get(url, timeout=self.timeout_seconds)

            # Если статус 4xx или 5xx — бросить исключение HTTPError.
            # Аналог RestAssured: .then().statusCode(200), только бросает ошибку сама.
            response.raise_for_status()

        # `except ТипОшибки as e:` — поймать ошибку этого типа и положить её в e.
        # Аналог Java: catch (ConnectException e).
        # requests.exceptions.ConnectionError — сервер не отвечает
        # (Ollama не запущена, неверный порт).
        except requests.exceptions.ConnectionError as e:
            # raise — бросить исключение (аналог throw).
            # `from e` — сохранить исходную ошибку как ПРИЧИНУ.
            # Аналог Java: throw new OllamaUnavailableException("...", e);
            raise OllamaUnavailableError(
                f"Ollama не отвечает по адресу {self.base_url}. "
                "Проверь, что Ollama запущена (иконка ламы в трее) "
                "и что в браузере открывается http://localhost:11434"
            ) from e
        except requests.exceptions.Timeout as e:
            raise OllamaUnavailableError(
                f"Ollama не ответила за {self.timeout_seconds} с по адресу {url}"
            ) from e

        # .json() — разобрать тело ответа из JSON в словари/списки Python.
        # Аналог RestAssured: response.as(Map.class) / Jackson readValue.
        return response.json()

    def get_version(self) -> str:
        # Ответ /api/version выглядит так: {"version": "0.20.4"}
        data = self._get("/api/version")
        return data.get("version", "unknown")

    # `-> list[ModelInfo]` — метод возвращает СПИСОК объектов ModelInfo.
    # Аналог Java: List<ModelInfo>.
    def list_models(self) -> list[ModelInfo]:
        # Ответ /api/tags: {"models": [ {...модель 1...}, {...модель 2...} ]}
        data = self._get("/api/tags")

        # Создаём пустой список. Аналог: List<ModelInfo> result = new ArrayList<>();
        result: list[ModelInfo] = []

        # Цикл «для каждого элемента». Аналог Java: for (Map item : models) {...}
        for item in data.get("models", []):
            # .append(x) — добавить в конец списка. Аналог list.add(x).
            result.append(ModelInfo.from_api(item))

        return result

    def list_running_models(self) -> list[RunningModel]:
        # Ответ /api/ps: {"models": [ {...загруженная модель...} ]}
        # Если ничего не загружено — список пустой.
        data = self._get("/api/ps")
        result: list[RunningModel] = []
        for item in data.get("models", []):
            result.append(RunningModel.from_api(item))
        return result
