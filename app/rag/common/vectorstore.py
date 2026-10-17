import time
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.core.config import get_settings

settings = get_settings()


_embeddings = None
_index = None
_stores: dict[str, PineconeVectorStore] = {}


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        if not settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY is missing")
        _embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model,
            google_api_key=settings.google_api_key,
            output_dimensionality=settings.embedding_dimension,
        )
    return _embeddings


def _index_dimension(index_info):
    dimension = getattr(index_info, "dimension", None)
    if dimension is None and isinstance(index_info, dict):
        dimension = index_info.get("dimension")
    return dimension


def ensure_index():
    """Return the Pinecone index, creating it if needed. Never deletes an existing index."""
    global _index
    if _index is not None:
        return _index
    if not settings.pinecone_api_key:
        raise RuntimeError("PINECONE_API_KEY is missing")
    name = settings.pinecone_index_name
    desired = settings.embedding_dimension
    pc = Pinecone(api_key=settings.pinecone_api_key)

    if name in [x["name"] for x in pc.list_indexes()]:
        current = _index_dimension(pc.describe_index(name))
        if current is not None and current != desired:
            raise RuntimeError(
                f"Pinecone index '{name}' has dimension {current} but EMBEDDING_DIMENSION is {desired}. "
                "Set EMBEDDING_DIMENSION to match, use another PINECONE_INDEX_NAME, "
                "or delete the index manually."
            )
    else:
        pc.create_index(
            name=name,
            dimension=desired,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        while not pc.describe_index(name).status["ready"]:
            time.sleep(1)

    _index = pc.Index(name)
    return _index


def get_vectorstore(namespace: str) -> PineconeVectorStore:
    if namespace not in _stores:
        _stores[namespace] = PineconeVectorStore(
            index=ensure_index(),
            embedding=get_embeddings(),
            namespace=namespace,
        )
    return _stores[namespace]


def get_retriever(namespace: str):
    return get_vectorstore(namespace).as_retriever(search_kwargs={"k": settings.top_k})


def add_documents(chunks, namespace: str, ids: list[str] | None = None):
    """Upsert chunks; reusing the same ids replaces the previous vectors."""
    return get_vectorstore(namespace).add_documents(chunks, ids=ids)


def delete_vectors(ids: list[str], namespace: str) -> None:
    if ids:
        get_vectorstore(namespace).delete(ids=ids, namespace=namespace)
