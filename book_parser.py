import os
import re
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import ebooklib
from ebooklib import epub

def clean_text(text: str) -> str:
    """Normalize text: remove excessive whitespace, normalize quotes and dashes."""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Remove soft hyphens and fix broken hyphenated words at line ends
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    # Convert multiple blank lines to double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove stray non-printable control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text.strip()

def estimate_duration_seconds(word_count: int, words_per_minute: int = 150) -> float:
    """Estimate speech duration in seconds given word count."""
    return (word_count / words_per_minute) * 60.0

class BookParser:
    @staticmethod
    def parse_epub(file_path: str, output_dir: str) -> Dict[str, Any]:
        """Extract metadata, cover image, and chapters from an EPUB file with fallback for malformed files."""
        book_id = str(uuid.uuid4())[:8]
        book_dir = os.path.join(output_dir, book_id)
        os.makedirs(book_dir, exist_ok=True)

        try:
            book = epub.read_epub(file_path)
            
            # 1. Metadata
            title_meta = book.get_metadata('DC', 'title')
            title = title_meta[0][0] if title_meta else Path(file_path).stem
            
            creator_meta = book.get_metadata('DC', 'creator')
            author = creator_meta[0][0] if creator_meta else "Unknown Author"

            # 2. Cover image extraction
            cover_path = None
            cover_items = list(book.get_items_of_type(ebooklib.ITEM_COVER))
            if not cover_items:
                for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                    name = item.get_name().lower()
                    if 'cover' in name:
                        cover_items.append(item)
                        break

            if cover_items:
                cover_item = cover_items[0]
                ext = os.path.splitext(cover_item.get_name())[1] or ".jpg"
                cover_full_path = os.path.join(book_dir, f"cover{ext}")
                with open(cover_full_path, "wb") as f:
                    f.write(cover_item.get_content())
                cover_path = cover_full_path

            # 3. Chapter extraction from spine & documents
            chapters = []
            chap_idx = 1

            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                content = item.get_content().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(content, 'html.parser')

                for tag in soup(['script', 'style', 'nav']):
                    tag.decompose()

                header = soup.find(['h1', 'h2', 'h3'])
                if header and header.get_text(strip=True):
                    chapter_title = header.get_text(strip=True)
                else:
                    chapter_title = f"Section {chap_idx}"

                paragraphs = []
                for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']):
                    ptxt = p.get_text(strip=True)
                    if ptxt:
                        paragraphs.append(ptxt)

                full_text = clean_text("\n\n".join(paragraphs))
                words = full_text.split()
                if len(words) < 5:
                    continue

                chapters.append({
                    "id": chap_idx,
                    "title": chapter_title[:100],
                    "word_count": len(words),
                    "char_count": len(full_text),
                    "text": full_text,
                    "selected": True
                })
                chap_idx += 1

            if chapters:
                total_words = sum(c["word_count"] for c in chapters)
                return {
                    "book_id": book_id,
                    "title": str(title).strip(),
                    "author": str(author).strip(),
                    "format": "epub",
                    "cover_path": cover_path,
                    "total_words": total_words,
                    "total_characters": sum(c["char_count"] for c in chapters),
                    "estimated_duration_sec": estimate_duration_seconds(total_words),
                    "chapters": chapters
                }

        except Exception as e:
            print(f"[BookParser] ebooklib parse notice: {e}, using zipfile fallback")

        # Fallback: Parse directly via zipfile
        import zipfile
        chapters = []
        cover_path = None
        title = Path(file_path).stem
        author = "Unknown Author"
        chap_idx = 1

        with zipfile.ZipFile(file_path, 'r') as z:
            # Look for cover image
            for name in z.namelist():
                low = name.lower()
                if 'cover' in low and any(low.endswith(x) for x in ['.jpg', '.jpeg', '.png']):
                    ext = os.path.splitext(name)[1]
                    cover_full_path = os.path.join(book_dir, f"cover{ext}")
                    with open(cover_full_path, "wb") as cf:
                        cf.write(z.read(name))
                    cover_path = cover_full_path
                    break

            # Process html/xhtml documents
            doc_names = [n for n in z.namelist() if n.lower().endswith(('.html', '.xhtml', '.htm'))]
            doc_names.sort()

            for name in doc_names:
                content = z.read(name).decode('utf-8', errors='ignore')
                soup = BeautifulSoup(content, 'html.parser')
                for tag in soup(['script', 'style', 'nav']):
                    tag.decompose()

                header = soup.find(['h1', 'h2', 'h3'])
                chapter_title = header.get_text(strip=True) if header and header.get_text(strip=True) else f"Chapter {chap_idx}"

                paragraphs = [p.get_text(strip=True) for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']) if p.get_text(strip=True)]
                full_text = clean_text("\n\n".join(paragraphs))
                words = full_text.split()
                if len(words) < 5:
                    continue

                chapters.append({
                    "id": chap_idx,
                    "title": chapter_title[:100],
                    "word_count": len(words),
                    "char_count": len(full_text),
                    "text": full_text,
                    "selected": True
                })
                chap_idx += 1

        total_words = sum(c["word_count"] for c in chapters)
        return {
            "book_id": book_id,
            "title": title,
            "author": author,
            "format": "epub",
            "cover_path": cover_path,
            "total_words": total_words,
            "total_characters": sum(c["char_count"] for c in chapters),
            "estimated_duration_sec": estimate_duration_seconds(total_words),
            "chapters": chapters
        }

    @staticmethod
    def parse_pdf(file_path: str, output_dir: str) -> Dict[str, Any]:
        """Extract metadata, cover image, and chapters from a PDF file using PyMuPDF."""
        doc = fitz.open(file_path)
        book_id = str(uuid.uuid4())[:8]
        book_dir = os.path.join(output_dir, book_id)
        os.makedirs(book_dir, exist_ok=True)

        meta = doc.metadata or {}
        title = meta.get("title") or Path(file_path).stem
        author = meta.get("author") or "Unknown Author"

        # 1. Render Page 0 as Cover Image
        cover_path = None
        if len(doc) > 0:
            page0 = doc[0]
            pix = page0.get_pixmap(dpi=150)
            cover_full_path = os.path.join(book_dir, "cover.png")
            pix.save(cover_full_path)
            cover_path = cover_full_path

        # 2. Extract chapters from bookmarks / TOC if available
        toc = doc.get_toc() # [[lvl, title, page_num], ...]
        chapters = []

        if toc and len(toc) > 1:
            # Build chapters based on TOC ranges
            for i, item in enumerate(toc):
                lvl, chap_title, start_page = item
                # 1-indexed to 0-indexed
                start_p = max(0, start_page - 1)
                end_p = len(doc) - 1
                if i + 1 < len(toc):
                    end_p = max(start_p, toc[i + 1][2] - 2)

                text_parts = []
                for pno in range(start_p, min(end_p + 1, len(doc))):
                    text_parts.append(doc[pno].get_text())

                chapter_text = clean_text("\n\n".join(text_parts))
                words = chapter_text.split()
                if len(words) >= 5:
                    chapters.append({
                        "id": i + 1,
                        "title": chap_title.strip()[:100],
                        "word_count": len(words),
                        "char_count": len(chapter_text),
                        "text": chapter_text,
                        "selected": True
                    })

        # If no TOC or empty TOC, group pages into chapters (~10 pages per chapter or heading detection)
        if not chapters:
            pages_per_chunk = 10
            for chunk_idx, start_page in enumerate(range(0, len(doc), pages_per_chunk), start=1):
                text_parts = []
                end_page = min(start_page + pages_per_chunk, len(doc))
                for pno in range(start_page, end_page):
                    text_parts.append(doc[pno].get_text())

                chapter_text = clean_text("\n\n".join(text_parts))
                words = chapter_text.split()
                if len(words) >= 5:
                    chapters.append({
                        "id": chunk_idx,
                        "title": f"Part {chunk_idx} (Pages {start_page + 1}-{end_page})",
                        "word_count": len(words),
                        "char_count": len(chapter_text),
                        "text": chapter_text,
                        "selected": True
                    })

        doc.close()
        total_words = sum(c["word_count"] for c in chapters)
        return {
            "book_id": book_id,
            "title": str(title).strip(),
            "author": str(author).strip(),
            "format": "pdf",
            "cover_path": cover_path,
            "total_words": total_words,
            "total_characters": sum(c["char_count"] for c in chapters),
            "estimated_duration_sec": estimate_duration_seconds(total_words),
            "chapters": chapters
        }

    @staticmethod
    def parse_txt(file_path: str, output_dir: str) -> Dict[str, Any]:
        """Extract chapters from plain text or markdown files."""
        book_id = str(uuid.uuid4())[:8]
        book_dir = os.path.join(output_dir, book_id)
        os.makedirs(book_dir, exist_ok=True)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                raw_text = f.read()

        title = Path(file_path).stem
        clean_content = clean_text(raw_text)

        # Regex to split on "Chapter 1", "CHAPTER I", "## Chapter 1", etc.
        pattern = r'(?m)^(?:#{1,3}\s+|chapter\s+\d+|chapter\s+[ivxlcdm]+|part\s+\d+).*$'
        matches = list(re.finditer(pattern, clean_content, re.IGNORECASE))

        chapters = []
        if matches:
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(clean_content)
                sec_text = clean_content[start:end].strip()
                lines = sec_text.split('\n', 1)
                chap_title = lines[0].strip('# \t\r')
                body = lines[1].strip() if len(lines) > 1 else ""

                words = body.split()
                if len(words) >= 5:
                    chapters.append({
                        "id": i + 1,
                        "title": chap_title[:100],
                        "word_count": len(words),
                        "char_count": len(body),
                        "text": body,
                        "selected": True
                    })

        # Fallback if no chapter headers found: chunk by words (~2,500 words per chapter)
        if not chapters:
            words = clean_content.split()
            chunk_size = 2500
            for idx, start_w in enumerate(range(0, len(words), chunk_size), start=1):
                chunk_words = words[start_w:start_w + chunk_size]
                text = " ".join(chunk_words)
                chapters.append({
                    "id": idx,
                    "title": f"Chapter {idx}",
                    "word_count": len(chunk_words),
                    "char_count": len(text),
                    "text": text,
                    "selected": True
                })

        total_words = sum(c["word_count"] for c in chapters)
        return {
            "book_id": book_id,
            "title": title,
            "author": "Unknown Author",
            "format": "txt",
            "cover_path": None,
            "total_words": total_words,
            "total_characters": sum(c["char_count"] for c in chapters),
            "estimated_duration_sec": estimate_duration_seconds(total_words),
            "chapters": chapters
        }

    @classmethod
    def parse_book(cls, file_path: str, output_dir: str) -> Dict[str, Any]:
        """Dispatch book parsing based on file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".epub":
            return cls.parse_epub(file_path, output_dir)
        elif ext == ".pdf":
            return cls.parse_pdf(file_path, output_dir)
        elif ext in [".txt", ".md", ".text"]:
            return cls.parse_txt(file_path, output_dir)
        else:
            raise ValueError(f"Unsupported book format: {ext}. Please upload EPUB, PDF, or TXT.")
