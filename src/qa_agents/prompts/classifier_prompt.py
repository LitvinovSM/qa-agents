"""Промпт классификатора падений: системная инструкция и few-shot примеры."""

SYSTEM_PROMPT = """Ты классификатор упавших автотестов. Определи ОДИН класс падения:
- product_bug: тестируемое приложение работает неправильно (неверные данные в ответе, 5xx, исключение внутри сервиса).
- flaky: нестабильность самого теста (тайминги, асинхронность, гонки, элемент UI ещё не готов).
- environment: недоступна инфраструктура (сервис/БД/брокер не отвечает, DNS, сеть, сертификаты).
- test_data: неверные или отсутствующие тестовые данные (нет записи из фикстуры, дубль ключа при подготовке, кривой файл данных).

Ответь JSON-объектом с полями:
- reasoning: 1-2 предложения на русском, почему этот класс;
- evidence: ДОСЛОВНАЯ цитата из текста падения (скопируй фрагмент, не пересказывай);
- category: один из product_bug, flaky, environment, test_data;
- confidence: число от 0 до 1."""

# Примеры «текст падения -> правильный ответ». Не пересекаются с data/sample_failures.json.
FEW_SHOT_EXAMPLES = [
    (
        (
            "org.postgresql.util.PSQLException: Connection to db-test:5432 refused. "
            "Check that the hostname and port are correct."
        ),
        {
            "reasoning": "БД тестового стенда не принимает подключения, код продукта не выполнялся.",
            "evidence": "Connection to db-test:5432 refused",
            "category": "environment",
            "confidence": 0.95,
        },
    ),
    (
        (
            "java.lang.AssertionError: Expected status code <200> but was <500>. Response: "
            '{"error": "NullPointerException at TransferService.calculateFee"}'
        ),
        {
            "reasoning": "Сервис упал с исключением внутри своей бизнес-логики и вернул 500.",
            "evidence": "NullPointerException at TransferService.calculateFee",
            "category": "product_bug",
            "confidence": 0.9,
        },
    ),
    (
        (
            "org.openqa.selenium.StaleElementReferenceException: stale element reference: "
            "element is not attached to the page document"
        ),
        {
            "reasoning": "Тест обратился к элементу, который страница успела перерисовать: гонка.",
            "evidence": "stale element reference: element is not attached to the page document",
            "category": "flaky",
            "confidence": 0.8,
        },
    ),
    (
        (
            "java.lang.IllegalArgumentException: Невалидный ИНН '123' в файле testdata/clients.csv, "
            "строка 14"
        ),
        {
            "reasoning": "Ошибка в файле тестовых данных, до проверки продукта дело не дошло.",
            "evidence": "Невалидный ИНН '123' в файле testdata/clients.csv",
            "category": "test_data",
            "confidence": 0.9,
        },
    ),
]
