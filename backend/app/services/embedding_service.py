from langchain_community.embeddings import HuggingFaceEmbeddings


def get_embedding_model():
    """
    Создаёт модель эмбеддингов.
    Работает ЛОКАЛЬНО
    """
    return HuggingFaceEmbeddings(
        # Маленькая но хорошая модель
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",

        # Настройки
        model_kwargs={"device": "cpu"},   # на CPU (в Docker)
        encode_kwargs={"normalize_embeddings": True},
    )