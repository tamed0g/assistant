"""
Сервис обработки документов.

Что делает:
1. Читает файл (PDF, TXT, MD)
2. Извлекает текст
3. Разбивает на кусочки (чанки)

LangChain TextSplitter умнее нашего старого кода:
- Режет по абзацам, потом по предложениям
- Не режет посреди слова
- Добавляет перекрытие (overlap) между кусочками
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from io import BytesIO


def extract_text(content: bytes, filename: str) -> str:
    """
    Извлекает текст из файла.

    content  — содержимое файла в байтах (как его прислал браузер)
    filename — имя файла ("report.pdf")

    Возвращает: строку с текстом
    """
    name = filename.lower()

    if name.endswith(".pdf"):
        # PDF → текст через библиотеку pypdf
        reader = PdfReader(BytesIO(content))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)

    elif name.endswith((".txt", ".md")):
        # Текстовый файл → просто декодируем байты в строку
        return content.decode("utf-8")

    else:
        raise ValueError(f"Формат не поддерживается: {filename}")


def split_into_chunks(text: str) -> list[str]:
    """
    Разбивает текст на кусочки.

    Пример:
        Вход: "Длинный текст на 5000 символов..."
        Выход: ["кусок 1 (500 символов)", "кусок 2 (500 символов)", ...]

    RecursiveCharacterTextSplitter пробует резать:
        1. По абзацам (\\n\\n)
        2. По строкам (\\n)
        3. По предложениям (. ! ?)
        4. По пробелам
        5. По буквам (крайний случай)
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,        # максимум символов в кусочке
        chunk_overlap=50,      # перекрытие между кусочками
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    )

    return splitter.split_text(text)