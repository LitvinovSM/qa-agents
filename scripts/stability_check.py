from qa_agents.ollama_client import OllamaClient

role = {"role": "system", "content": "Ты классификатор падений автотестов. Отвечай ОДНИМ словом из списка: "}
client = OllamaClient()
question = "Ошибка NullPointerException это проблема автотестов или ПО?"

print("ПРОВЕРКА НИЗКОЙ ТЕМПЕРАТУРЫ:")
for i in range(5):
    full_question = {"role": "user", "content": question}
    response = client.chat([role,full_question],temperature=0.0)
    print(f"Ответ модели: {response.content}")

print("ПРОВЕРКА ВЫСОКОЙ ТЕМПЕРАТУРЫ:")
for i in range(5):
    full_question = {"role": "user", "content": question}
    response = client.chat([role,full_question], temperature=1.0)
    print(f"Ответ модели: {response.content}")
