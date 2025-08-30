import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    azure_openai_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    embedding_deployment: str = os.getenv("EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "2000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    faiss_index_path: str = os.getenv("FAISS_INDEX_PATH", "data/index/faiss_index")
    workspace_dir: str = os.getenv("WORKSPACE_DIR", "data/workspace")
    spotbugs_path: str = os.getenv("SPOTBUGS_PATH", "spotbugs")
    maven_bin: str = os.getenv("MAVEN_BIN", "mvn")
    # LLM batching/tuning
    map_batch_size: int = int(os.getenv("MAP_BATCH_SIZE", "15"))
    reduce_group_size: int = int(os.getenv("REDUCE_GROUP_SIZE", "15"))
    reduce_sleep_secs: float = float(os.getenv("REDUCE_SLEEP_SECS", "0.5"))
    maven_bin: str = os.getenv("MAVEN_BIN", "mvn")

settings = Settings()

