import os
from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
import faiss
import numpy as np
import pickle

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# храним индексы и чанки для каждого юзера
indexes = {}
chunks_store = {}


def get_embedding(text: str) -> list:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def add_document(user_id: str, text: str):
    # разбиваем текст на чанки
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)

    if not chunks:
        return

    # получаем эмбеддинги для всех чанков
    embeddings = [get_embedding(chunk) for chunk in chunks]
    embeddings_np = np.array(embeddings, dtype="float32")

    # создаем или обновляем FAISS индекс для этого юзера
    dim = len(embeddings[0])

    if user_id not in indexes:
        indexes[user_id] = faiss.IndexFlatL2(dim)
        chunks_store[user_id] = []

    indexes[user_id].add(embeddings_np)
    chunks_store[user_id].extend(chunks)


def ask(user_id: str, question: str) -> str:
    if user_id not in indexes or indexes[user_id].ntotal == 0:
        return "Сначала загрузи документ через /upload"

    # ищем похожие чанки
    question_embedding = np.array([get_embedding(question)], dtype="float32")
    k = min(3, indexes[user_id].ntotal)  # берем топ-3 или меньше если документов мало
    distances, indices = indexes[user_id].search(question_embedding, k)

    # собираем контекст
    context_chunks = [chunks_store[user_id][i] for i in indices[0]]
    context = "\n\n".join(context_chunks)

    # отправляем в GPT
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Отвечай на вопрос только на основе предоставленного контекста. Если ответа нет в контексте — скажи об этом."
            },
            {
                "role": "user",
                "content": f"Контекст:\n{context}\n\nВопрос: {question}"
            }
        ]
    )

    return response.choices[0].message.content


def clear_user(user_id: str):
    if user_id in indexes:
        del indexes[user_id]
        del chunks_store[user_id]
