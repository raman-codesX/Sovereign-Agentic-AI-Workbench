import os

from tools.docx_tool import extract_text_from_docx
from tools.pdf_tool import extract_text_from_pdf
from tools.file_tool import read_file

def extract_file(file_path):
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)

    if extension in [".md", ".txt"]:
        return read_file(file_path)

    if extension == ".docx":
        return extract_text_from_docx(file_path)

    raise ValueError(
        f"Unsupported file type: {extension}"
    )