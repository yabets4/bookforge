import os
import shutil
import tempfile
import sys
from pathlib import Path

# Add compiler directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from book_parser import BookParser
import ebooklib
from ebooklib import epub
import fitz

def test_txt_parser():
    with tempfile.TemporaryDirectory() as tmpdir:
        sample_txt = Path(tmpdir) / "sample_story.txt"
        sample_txt.write_text(
            "# Chapter 1: The Beginning\n\nOnce upon a time in a digital realm, algorithms roamed freely.\n"
            "They processed data at the speed of light.\n\n"
            "# Chapter 2: The Forge\n\nInside the GPU compiler, neural networks synthesized voices with uncanny realism.\n"
            "Every sentence sounded alive.",
            encoding="utf-8"
        )
        res = BookParser.parse_txt(str(sample_txt), tmpdir)
        assert res["title"] == "sample_story"
        assert len(res["chapters"]) == 2
        assert "Chapter 1" in res["chapters"][0]["title"]
        assert "Chapter 2" in res["chapters"][1]["title"]
        assert res["total_words"] > 0
        print("✓ TXT Parser passed")

def test_epub_parser():
    with tempfile.TemporaryDirectory() as tmpdir:
        book = epub.EpubBook()
        book.set_title("Test Chronicles")
        book.add_author("Jane Author")

        c1 = epub.EpubHtml(title="Introduction", file_name="chap_01.xhtml", lang="en")
        c1.content = "<h1>Chapter 1: Dawn</h1><p>The dawn was crisp and quiet across the valley.</p>"
        book.add_item(c1)

        c2 = epub.EpubHtml(title="The Journey", file_name="chap_02.xhtml", lang="en")
        c2.content = "<h1>Chapter 2: The Road</h1><p>They packed their bags and walked toward the distant mountains.</p>"
        book.add_item(c2)

        # Add default NCX and Nav
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        book.spine = ["nav", c1, c2]

        epub_path = os.path.join(tmpdir, "test_book.epub")
        epub.write_epub(epub_path, book)

        res = BookParser.parse_epub(epub_path, tmpdir)
        assert res["title"] == "Test Chronicles"
        assert res["author"] == "Jane Author"
        assert len(res["chapters"]) >= 2
        print("✓ EPUB Parser passed")

def test_pdf_parser():
    with tempfile.TemporaryDirectory() as tmpdir:
        doc = fitz.open()
        p1 = doc.new_page()
        p1.insert_text((50, 50), "Chapter 1: The Awakening\n\nHe woke up to the sound of rain against the window.")
        p2 = doc.new_page()
        p2.insert_text((50, 50), "Chapter 2: Moving Forward\n\nThe city streets were wet and reflected neon lights.")

        pdf_path = os.path.join(tmpdir, "test_doc.pdf")
        doc.save(pdf_path)
        doc.close()

        res = BookParser.parse_pdf(pdf_path, tmpdir)
        assert len(res["chapters"]) >= 1
        assert res["format"] == "pdf"
        assert os.path.exists(res["cover_path"])
        print("✓ PDF Parser passed")

if __name__ == "__main__":
    test_txt_parser()
    test_epub_parser()
    test_pdf_parser()
    print("All parser tests successfully passed!")
