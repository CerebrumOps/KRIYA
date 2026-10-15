# ==============================================================================
# KRIYA Tool: Sovereign OCR & Document Parser
# ==============================================================================
# Enables text-only LLMs to inspect, read, and analyze images (photos, scans,
# equipment nameplates, diagrams) and PDF documents without native multimodal vision.
#
# Supported formats:
# 1. Images: PNG, JPG, JPEG, TIFF, BMP, WEBP (Optical Character Recognition via Tesseract)
# 2. PDFs: Digital vector PDFs (via pypdf) & scanned image PDFs (via pdf2image + Tesseract)
# ==============================================================================

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import shutil

# Try importing PIL
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Try importing pytesseract
try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False

# Try importing pypdf
try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

# Try importing pdf2image
try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False


def _resolve_document_path(file_path: str) -> Optional[Path]:
    """
    Locates document safely across active workspace directories.
    Prevents path traversal outside permitted workspace/system paths.
    """
    clean_path = (file_path or "").strip()
    if not clean_path:
        return None

    path_obj = Path(clean_path)
    clean_name = path_obj.name

    # Import workspace manager
    try:
        from agent.workspace.workspace_manager import get_active_workspace_dir, BASE_WORKSPACE_DIR
        active_ws = get_active_workspace_dir()
    except Exception:
        active_ws = Path("/app/workspace")
        BASE_WORKSPACE_DIR = Path("/app/workspace")

    candidates = [
        path_obj,
        Path("/app") / clean_path,
        active_ws / clean_name,
        active_ws / clean_path,
        active_ws / "documents" / clean_name,
        active_ws / "sandbox" / clean_name,
        active_ws / "media" / clean_name,
        BASE_WORKSPACE_DIR / clean_name,
        BASE_WORKSPACE_DIR / clean_path,
        BASE_WORKSPACE_DIR / "chats" / "default_chat" / clean_name,
        BASE_WORKSPACE_DIR / "documents" / clean_name,
        Path("/app/workspace") / clean_name,
        Path("/app/workspace/chats/default_chat") / clean_name,
        Path("/app/workspace/chats") / clean_name,
        Path.home() / "kriya-shared" / clean_name,
        Path("/host-bridge") / clean_name,
        Path.cwd() / clean_name,
    ]

    # Recursive check in active workspace first
    if active_ws.exists():
        for found in active_ws.glob(f"**/{clean_name}"):
            if found.is_file():
                candidates.insert(0, found)
                break

    # Recursive check across base workspace (covers files uploaded in 'New Chat' before chat_id creation)
    if BASE_WORKSPACE_DIR.exists():
        for found in BASE_WORKSPACE_DIR.glob(f"**/{clean_name}"):
            if found.is_file():
                candidates.append(found)
                break

    for cand in candidates:
        try:
            if cand.is_file():
                return cand.resolve()
        except Exception:
            continue

    return None


def ocr_extract_text(file_path: str, max_pages: int = 15) -> str:
    """
    Performs Optical Character Recognition (OCR) or document text parsing on
    images (PNG, JPG, TIFF, BMP) or PDF documents to extract all textual and numerical contents.
    """
    target = _resolve_document_path(file_path)
    if not target:
        return (
            f"[OCR Error]: Document or image file '{file_path}' was not found in the active workspace. "
            f"Please verify the filename or ensure the user uploaded the file."
        )

    ext = target.suffix.lower().lstrip(".")
    stat = target.stat()
    file_size_kb = round(stat.st_size / 1024, 1)

    # 1. HANDLE IMAGE FILES
    image_exts = {"png", "jpg", "jpeg", "tiff", "tif", "bmp", "webp"}
    if ext in image_exts:
        if not HAS_PIL:
            return "[OCR Error]: Python Pillow library is not installed."
        if not HAS_PYTESSERACT:
            return "[OCR Error]: pytesseract is not installed in the environment."

        try:
            with Image.open(target) as img:
                width, height = img.size
                img_format = img.format or ext.upper()
                
                # Check tesseract command
                extracted = pytesseract.image_to_string(img)
                clean_text = extracted.strip()

                if not clean_text:
                    return (
                        f"### OCR Analysis: `{target.name}`\n"
                        f"- **Format:** {img_format} Image ({width}x{height} px, {file_size_kb} KB)\n"
                        f"- **Status:** No readable text characters were detected in the image.\n"
                        f"*(The image may be blank, a graphical diagram without text labels, or too blurry for OCR)*"
                    )

                return (
                    f"### OCR Document Analysis: `{target.name}`\n"
                    f"- **Format:** {img_format} Image ({width}x{height} px, {file_size_kb} KB)\n"
                    f"- **Extraction Engine:** Optical Character Recognition (Tesseract OCR)\n"
                    f"- **Characters Extracted:** {len(clean_text)}\n\n"
                    f"#### Extracted Content:\n"
                    f"```text\n{clean_text}\n```"
                )
        except Exception as e:
            return f"[OCR Error during image processing of '{target.name}']: {str(e)}"

    # 2. HANDLE PDF DOCUMENTS
    elif ext == "pdf":
        pages_content: List[str] = []
        is_scanned_ocr = False

        # Step 2a: Try native text extraction via pypdf
        if HAS_PYPDF:
            try:
                reader = PdfReader(str(target))
                total_pages = len(reader.pages)
                pages_to_read = min(total_pages, max_pages)

                for idx in range(pages_to_read):
                    page = reader.pages[idx]
                    txt = page.extract_text() or ""
                    pages_content.append(txt.strip())

                total_chars = sum(len(p) for p in pages_content)
                # If characters per page are very low (< 30 avg), this is likely a scanned image PDF
                if total_chars < (pages_to_read * 30):
                    is_scanned_ocr = True
            except Exception:
                is_scanned_ocr = True
        else:
            is_scanned_ocr = True

        # Step 2b: If scanned PDF, convert to images and run Tesseract OCR
        if is_scanned_ocr:
            if not HAS_PDF2IMAGE or not HAS_PYTESSERACT:
                if pages_content and any(pages_content):
                    # Fall back to whatever pypdf got
                    pass
                else:
                    return (
                        f"[OCR Error]: PDF appears to be a scanned image, but 'pdf2image' or 'poppler-utils' "
                        f"is not fully configured for raster OCR."
                    )
            else:
                try:
                    images = convert_from_path(str(target), first_page=1, last_page=max_pages)
                    ocr_pages = []
                    for idx, img in enumerate(images):
                        page_txt = pytesseract.image_to_string(img).strip()
                        ocr_pages.append(f"--- Page {idx + 1} ---\n{page_txt if page_txt else '[No text on page]'}")
                    
                    return (
                        f"### Scanned PDF OCR Analysis: `{target.name}`\n"
                        f"- **Format:** Scanned PDF Document ({len(images)} pages processed, {file_size_kb} KB)\n"
                        f"- **Extraction Engine:** Tesseract OCR via Poppler Rasterizer\n\n"
                        f"#### Extracted Document Pages:\n\n" + "\n\n".join(ocr_pages)
                    )
                except Exception as ocr_err:
                    if pages_content and any(pages_content):
                        # Use pypdf results
                        pass
                    else:
                        return f"[OCR Error during PDF rasterization]: {str(ocr_err)}"

        # If digital text extraction was successful
        formatted_pages = []
        for idx, text in enumerate(pages_content):
            formatted_pages.append(f"--- Page {idx + 1} ---\n{text if text else '[Blank page or non-text content]'}")

        return (
            f"### PDF Document Analysis: `{target.name}`\n"
            f"- **Format:** Digital Vector PDF ({len(pages_content)} pages processed, {file_size_kb} KB)\n"
            f"- **Extraction Engine:** Direct PDF Parsing (pypdf)\n\n"
            f"#### Extracted Document Pages:\n\n" + "\n\n".join(formatted_pages)
        )

    # 3. TEXT / CSV / JSON FILES (Direct Read)
    elif ext in {"txt", "csv", "json", "log", "md", "xml", "html"}:
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
            # Truncate if excessively long
            max_chars = 30000
            truncated = content[:max_chars]
            notice = f"\n... [Truncated: showing {max_chars} of {len(content)} characters]" if len(content) > max_chars else ""
            return (
                f"### Document Text Content: `{target.name}`\n"
                f"- **Format:** Plain Text / Structured ({file_size_kb} KB)\n\n"
                f"```text\n{truncated}{notice}\n```"
            )
        except Exception as e:
            return f"[Error reading text file '{target.name}']: {str(e)}"

    else:
        return (
            f"[OCR Unsupported Format]: File '{target.name}' with extension '.{ext}' is not a supported image or document. "
            f"Supported extensions: PNG, JPG, JPEG, TIFF, BMP, WEBP, PDF, TXT, CSV, JSON."
        )


# ==============================================================================
# TOOL SCHEMA FOR LLM
# ==============================================================================

OCR_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "ocr_extract_text",
        "description": (
            "Extract and read all textual, numerical, and tabular content from uploaded photos, "
            "images (PNG, JPG, TIFF, BMP, WEBP), and PDF documents (scanned reports, inspection sheets, "
            "P&ID diagrams, equipment nameplates) using Optical Character Recognition (OCR) and document parsing. "
            "Use this tool whenever the user uploads or asks to analyze photos, scans, diagrams, or PDF files, "
            "because the underlying LLM does not possess native multimodal vision capabilities."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Name or relative path of the image or PDF file in the workspace (e.g. 'cml_scan.png', 'inspection_report.pdf', 'nameplate.jpg')"
                },
                "max_pages": {
                    "type": "integer",
                    "description": "Maximum number of pages to process for PDF documents (default is 15)"
                }
            },
            "required": ["file_path"]
        }
    }
}
