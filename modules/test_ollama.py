from langchain_ollama import ChatOllama


model = ChatOllama(
    model="llama3.2:3b",
    temperature=0.2
)


response = model.invoke(
    "Explain online examination integrity in two sentences."
)


print("=" * 60)
print("LANGCHAIN + OLLAMA TEST")
print("=" * 60)

print(response.content)

print("=" * 60)