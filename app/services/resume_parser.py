from pathlib import Path

from PyPDF2 import PdfReader
from docx import Document


def extract_text_from_file(file_path):
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix in (".docx", ".doc"):
        return _extract_docx(path)
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")

    return ""


def _extract_pdf(path):
    text_parts = []
    try:
        reader = PdfReader(str(path))
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text_parts.append(content)
    except Exception:
        return ""
    return "\n".join(text_parts).strip()


def _extract_docx(path):
    try:
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()
    except Exception:
        return ""
