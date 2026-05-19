import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from core.config import EMBEDDING_PATH, MODEL_PATH, DB_PATH

embedding = HuggingFaceEmbeddings(
    model_name=EMBEDDING_PATH,
    cache_folder=MODEL_PATH,
)

db = Chroma(persist_directory=DB_PATH, embedding_function=embedding)
results = db.similarity_search_with_score("LLM 是什么", k=10)

print("\n=== 检索结果 ===")
for i, (doc, score) in enumerate(results):
    print(f"\n结果 {i+1}: 分数={score:.4f}")
    print(f"内容: {doc.page_content[:150]}")
