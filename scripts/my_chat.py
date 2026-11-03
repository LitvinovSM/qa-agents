from qa_agents.ollama_client import OllamaClient

chat = [
    {"role": "system", "content": "Ты помощник QA-инженера. Отвечай кратко и по делу."}
]

while True:
    question = input("Ты: ").strip()

    if question == "/bye":
        break
    if question == "/print_history":
        print(*chat,sep="\n")
        continue
    if not question:
        continue
    client : OllamaClient = OllamaClient()
    chat.append({"role": "user", "content": question})

    chat_result = client.chat(chat)
    answer = chat_result.content  # заглушка, замени на ответ из result
    tokens = chat_result.input_tokens
    chat.append({"role": "assistant", "content": answer})
    print(f"Ответ модели:{answer}")
    print(f"Количество входящих токенов {tokens=}")

print("Чат завершён")