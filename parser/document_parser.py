import os
import re
from dataclasses import dataclass
from typing import List

from bs4 import BeautifulSoup
from ebooklib import epub
from pdfminer.high_level import extract_text
from mobi import Mobi
from docx import Document

try:  # pragma: no cover - optional dependency
    import textract
except ImportError:  # pragma: no cover - optional dependency
    textract = None


@dataclass
class Chapter:
    title: str
    content: str


class DocumentParserError(Exception):
    """Custom exception for parser errors."""


class DocumentParser:
    """Parse different document types into chapters."""

    heading_pattern = re.compile(
        r"^(?:\s*)(?:(第[\d一二三四五六七八九十百千万零两]+[章节回部卷])|((?:chapter|section|part)\s+\d+))",
        re.IGNORECASE,
    )

    def parse(self, file_path: str) -> List[Chapter]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            text = self._parse_pdf(file_path)
            return self._split_into_chapters(text, default_title="PDF 章节")
        if ext == ".txt":
            text = self._parse_txt(file_path)
            return self._split_into_chapters(text, default_title="文本章节")
        if ext == ".epub":
            return self._parse_epub(file_path)
        if ext == ".mobi":
            return self._parse_mobi(file_path)
        if ext == ".doc":
            text = self._parse_doc(file_path)
            return self._split_into_chapters(text, default_title="Word 章节")
        if ext == ".docx":
            text = self._parse_docx(file_path)
            return self._split_into_chapters(text, default_title="Word 章节")
        raise DocumentParserError(f"暂不支持的文件类型: {ext}")

    def _parse_pdf(self, file_path: str) -> str:
        try:
            return extract_text(file_path)
        except Exception as exc:  # pragma: no cover - pdfminer specific errors
            raise DocumentParserError("解析 PDF 文件失败") from exc

    def _parse_txt(self, file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                return handle.read()
        except Exception as exc:
            raise DocumentParserError("读取文本文件失败") from exc

    def _parse_docx(self, file_path: str) -> str:
        try:
            document = Document(file_path)
        except Exception as exc:
            raise DocumentParserError("解析 Word 文件失败") from exc
        paragraphs = [para.text for para in document.paragraphs]
        return "\n".join(paragraphs)

    def _parse_doc(self, file_path: str) -> str:
        if textract is None:
            raise DocumentParserError("解析 DOC 文件需要安装 textract 依赖")
        try:
            content = textract.process(file_path)
        except Exception as exc:  # pragma: no cover - textract backend specific
            raise DocumentParserError("解析 DOC 文件失败") from exc
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("gb18030", errors="ignore")

    def _parse_epub(self, file_path: str) -> List[Chapter]:
        try:
            book = epub.read_epub(file_path)
        except Exception as exc:
            raise DocumentParserError("解析 EPUB 文件失败") from exc
        chapters: List[Chapter] = []
        for item in book.get_items_of_type(epub.ITEM_DOCUMENT):
            title = self._guess_title(item.get_name())
            soup = BeautifulSoup(item.get_body_content(), "html.parser")
            text = soup.get_text("\n")
            text = self._clean_text(text)
            if text.strip():
                chapters.append(Chapter(title=title, content=text))
        if not chapters:
            raise DocumentParserError("未能从 EPUB 文件中提取章节")
        return chapters

    def _parse_mobi(self, file_path: str) -> List[Chapter]:
        try:
            book = Mobi(file_path)
            book.parse()
            raw_html = book.get_raw_html()
            if isinstance(raw_html, bytes):
                raw_html = raw_html.decode("utf-8", errors="ignore")
        except Exception as exc:  # pragma: no cover - mobi parsing heavy
            raise DocumentParserError("解析 MOBI 文件失败") from exc
        soup = BeautifulSoup(raw_html, "html.parser")
        elements = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "div"])
        chapters: List[Chapter] = []
        current_title = "MOBI 章节"
        current_content: List[str] = []
        for element in elements:
            if element.name in {"h1", "h2", "h3"}:
                if current_content:
                    chapters.append(
                        Chapter(title=current_title.strip() or "MOBI 章节", content="\n".join(current_content).strip())
                    )
                    current_content = []
                current_title = self._clean_text(element.get_text(" "))
            else:
                current_content.append(self._clean_text(element.get_text(" ")))
        if current_content:
            chapters.append(
                Chapter(title=current_title.strip() or "MOBI 章节", content="\n".join(current_content).strip())
            )
        if not chapters:
            text = soup.get_text("\n")
            return self._split_into_chapters(text, default_title="MOBI 章节")
        return chapters

    def _split_into_chapters(self, text: str, default_title: str) -> List[Chapter]:
        cleaned = self._clean_text(text)
        lines = cleaned.splitlines()
        chapters: List[Chapter] = []
        current_title = None
        current_content: List[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                current_content.append("")
                continue
            if self.heading_pattern.match(stripped):
                if current_content:
                    chapters.append(
                        Chapter(
                            title=current_title or f"{default_title} {len(chapters) + 1}",
                            content="\n".join(current_content).strip(),
                        )
                    )
                    current_content = []
                current_title = stripped
            current_content.append(stripped)
        if current_content:
            chapters.append(
                Chapter(
                    title=current_title or (f"{default_title} {len(chapters) + 1}" if chapters else default_title),
                    content="\n".join(current_content).strip(),
                )
            )
        if len(chapters) <= 1:
            chunk_size = 1200
            text_length = len(cleaned)
            if text_length <= chunk_size:
                return [Chapter(title=default_title, content=cleaned.strip())]
            chapters = []
            for index in range(0, text_length, chunk_size):
                chunk = cleaned[index : index + chunk_size]
                chapters.append(
                    Chapter(title=f"{default_title} {len(chapters) + 1}", content=chunk.strip())
                )
        return chapters

    @staticmethod
    def _clean_text(text: str) -> str:
        return re.sub(r"\u3000", " ", text).replace("\r", "")

    @staticmethod
    def _guess_title(name: str) -> str:
        base = os.path.basename(name)
        title = os.path.splitext(base)[0]
        return title or "EPUB 章节"


__all__ = ["DocumentParser", "Chapter", "DocumentParserError"]
