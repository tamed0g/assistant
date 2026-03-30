import logging
from io import BytesIO
from typing import List

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def extract_text(content: bytes, filename: str) -> str:
    """
    Извлекает сырой текст из файлов (PDF, TXT, MD).
    """
    name = filename.lower()
    logger.info(f"Extracting text from document: {filename}")

    try:
        if name.endswith(".pdf"):
            reader = PdfReader(BytesIO(content))
            pages = [page.extract_text() for page in reader.pages if page.extract_text()]
            return "\n\n".join(pages)

        elif name.endswith((".txt", ".md")):
            return content.decode("utf-8")

        else:
            logger.error(f"Unsupported file format attempted: {filename}")
            raise ValueError(f"Unsupported file format: {filename}")
            
    except Exception as e:
        logger.error(f"Error extracting text from {filename}: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to extract text from {filename}: {str(e)}")


def split_into_chunks(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Разбивает текст на семантические чанки с помощью LangChain.
    """
    logger.info(f"Splitting text into chunks (size={chunk_size}, overlap={chunk_overlap})...")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    )

    chunks = splitter.split_text(text)
    logger.info(f"Successfully generated {len(chunks)} chunks.")
    return chunks