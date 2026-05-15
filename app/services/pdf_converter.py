from typing import List

import fitz  # PyMuPDF


def pdf_to_images(pdf_bytes: bytes, max_pages: int = 20, dpi: int = 150) -> List[bytes]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    images = []
    for page_num in range(min(len(doc), max_pages)):
        pix = doc[page_num].get_pixmap(matrix=matrix, alpha=False)
        images.append(pix.tobytes("png"))
    doc.close()
    return images
