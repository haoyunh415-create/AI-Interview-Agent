import os

MODEL_PATH = "./models"
EMBEDDING_MODEL = "models--shibing624--text2vec-base-chinese"
EMBEDDING_SNAPSHOT = "183bb99aa7af74355fb58d16edf8c13ae7c5433e"
EMBEDDING_PATH = os.path.join(MODEL_PATH, EMBEDDING_MODEL, "snapshots", EMBEDDING_SNAPSHOT)

DB_PATH = "./chroma_db"
DATA_DIR = "./data"
KNOWLEDGE_FILE = os.path.join(DATA_DIR, "llm_pro_knowledge.txt")
AUTO_KB_FILE = os.path.join(DATA_DIR, "auto_kb.txt")

LLM_MODEL = "deepseek-chat"
LLM_BASE_URL = "https://api.deepseek.com"
LLM_TEMPERATURE = 0.7
LLM_TIMEOUT = 60
LLM_MAX_RETRIES = 2

CHUNK_SIZE = 250
CHUNK_OVERLAP = 40
RETRIEVAL_K = 1
RETRIEVAL_FETCH = 20
RETRIEVAL_SCORE_THRESHOLD = 180
