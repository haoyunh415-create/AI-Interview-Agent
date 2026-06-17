import os
import shutil

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.config import (
    AUTO_KB_FILE,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DB_PATH,
    EMBEDDING_PATH,
    KNOWLEDGE_FILE,
    MODEL_PATH,
)


def reset_knowledge_base():
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)

    all_docs = []
    knowledge_files = [KNOWLEDGE_FILE, AUTO_KB_FILE]
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n---\n", "\n## ", "\n# ", "\n\n", "\n", "。", "！", "？"],
    )

    for fpath in knowledge_files:
        if os.path.exists(fpath):
            loader = TextLoader(fpath, encoding="utf-8")
            documents = loader.load()
            docs = text_splitter.split_documents(documents)
            all_docs.extend(docs)
            print(f"  {fpath}: {len(docs)} 个片段")
        else:
            print(f"警告：跳过不存在的文件 {fpath}")

    print(f"总计切分为 {len(all_docs)} 个片段")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_PATH,
        cache_folder=MODEL_PATH,
    )

    Chroma.from_documents(
        documents=all_docs,
        embedding=embeddings,
        persist_directory=DB_PATH,
    )
    print("知识库加载完成！")


if __name__ == "__main__":
    reset_knowledge_base()
