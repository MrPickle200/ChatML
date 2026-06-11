from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    app_name: str = "ChatML"
    debug: bool = False

    # MongoDB
    mongodb_uri: str
    mongodb_database: str

    # Qdrant
    qdrant_host: str
    qdrant_port: int
    qdrant_collection_name: str
    qdrant_vector_size: int

    # Chunk
    chunk_size: int
    chunk_overlap: int

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()