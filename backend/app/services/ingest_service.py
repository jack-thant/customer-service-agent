from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass
from typing import Any, List
from urllib.parse import urljoin, urlparse

from app.services.chroma_client import get_chroma_client
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import settings


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://help.atome.ph/",
    "Connection": "keep-alive",
}


@dataclass
class ArticleDocument:
    url: str
    title: str
    category: str
    text: str


class KBIngestService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.chroma_client = get_chroma_client()
        self.collection = self.chroma_client.get_or_create_collection(
            name=settings.chroma_collection_name
        )
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(HEADERS)
        return session

    def ingest_category(self, category_url: str, force_reingest: bool = False) -> dict:
        article_links = self._extract_article_links(category_url)
        results = {
            "category_url": category_url,
            "article_links_found": len(article_links),
            "articles_ingested": 0,
            "articles_skipped": 0,
            "chunks_upserted": 0,
            "failed_urls": [],
        }

        for article_url in article_links:
            try:
                if not force_reingest and self._has_existing_embeddings(article_url):
                    results["articles_skipped"] += 1
                    continue

                chunks_written = self.ingest_article(article_url, force_reingest=force_reingest)
                results["articles_ingested"] += 1
                results["chunks_upserted"] += chunks_written
            except Exception:
                results["failed_urls"].append(article_url)

        return results

    def ingest_article(self, article_url: str, force_reingest: bool = False) -> int:
        if not force_reingest and self._has_existing_embeddings(article_url):
            return 0

        if force_reingest:
            self._delete_existing_embeddings(article_url)

        article = self._parse_article(article_url)
        if not article.text.strip():
            return 0

        chunks = self._chunk_text(article.text)
        if not chunks:
            return 0

        embeddings = self._embed_texts(chunks)

        ids: List[str] = []
        metadatas: List[dict] = []
        documents: List[str] = []

        for idx, chunk in enumerate(chunks):
            chunk_id = self._make_chunk_id(article.url, idx, chunk)
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append(
                {
                    "text": chunk,
                    "source_url": article.url,
                    "article_title": article.title,
                    "category": article.category,
                    "chunk_index": idx,
                }
            )

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(chunks)

    def _fetch_html(self, url: str) -> str:
        response = self.session.get(
            url,
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        return response.text

    def _extract_article_links(self, category_url: str) -> List[str]:
        links = self._extract_article_links_from_html(category_url)
        if links:
            return links[: settings.max_article_links]
        return self._extract_article_links_from_api(category_url)[: settings.max_article_links]

    def _extract_article_links_from_html(self, category_url: str) -> List[str]:
        try:
            html_text = self._fetch_html(category_url)
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code in {401, 403}:
                return []
            raise

        soup = BeautifulSoup(html_text, "html.parser")

        links = set()
        parsed_base = urlparse(category_url)
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"

        locale = self._extract_locale_from_path(parsed_base.path) or "en-gb"
        article_path_prefix = f"/hc/{locale}/articles/"

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            full_url = urljoin(base_domain, href)

            if article_path_prefix in full_url:
                links.add(full_url.split("?")[0])

        return sorted(links)

    def _extract_article_links_from_api(self, category_url: str) -> List[str]:
        parsed = urlparse(category_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        locale = self._extract_locale_from_path(parsed.path) or "en-gb"
        category_id = self._extract_category_id_from_path(parsed.path)
        if not category_id:
            return []

        links: list[str] = []
        page = 1

        while True:
            api_url = (
                f"{base_domain}/api/v2/help_center/{locale}/categories/"
                f"{category_id}/articles.json?page={page}&per_page=100"
            )
            response = self.session.get(api_url, timeout=settings.request_timeout_seconds)
            response.raise_for_status()
            payload = response.json()

            articles = payload.get("articles", [])
            if not articles:
                break

            for article in articles:
                html_url = article.get("html_url")
                if html_url:
                    links.append(html_url.split("?")[0])

            if not payload.get("next_page"):
                break
            page += 1

        return sorted(set(links))

    def _parse_article(self, article_url: str) -> ArticleDocument:
        try:
            html_text = self._fetch_html(article_url)
            return self._parse_article_from_html(article_url, html_text)
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code not in {401, 403}:
                raise
            return self._parse_article_from_api(article_url)

    def _parse_article_from_html(self, article_url: str, html_text: str) -> ArticleDocument:
        soup = BeautifulSoup(html_text, "html.parser")

        title = self._extract_title(soup)
        category = self._extract_category(soup)

        main_text = self._extract_main_content(soup)
        cleaned_text = self._normalize_text(main_text)

        return ArticleDocument(
            url=article_url,
            title=title,
            category=category,
            text=cleaned_text,
        )

    def _parse_article_from_api(self, article_url: str) -> ArticleDocument:
        parsed = urlparse(article_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        locale = self._extract_locale_from_path(parsed.path) or "en-gb"
        article_id = self._extract_article_id_from_path(parsed.path)
        if not article_id:
            raise ValueError(f"Could not extract article id from URL: {article_url}")

        api_url = f"{base_domain}/api/v2/help_center/{locale}/articles/{article_id}.json"
        response = self.session.get(api_url, timeout=settings.request_timeout_seconds)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        article_payload: dict[str, Any] = payload.get("article", {})

        title = self._normalize_text(str(article_payload.get("title", "Untitled Article")))
        category = "Atome Card"

        body_html = str(article_payload.get("body", ""))
        body_soup = BeautifulSoup(body_html, "html.parser")
        parts: list[str] = []
        for element in body_soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
            text = self._normalize_text(element.get_text(" ", strip=True))
            if text:
                parts.append(text)

        if not parts:
            fallback_text = self._normalize_text(html.unescape(body_soup.get_text(" ", strip=True)))
            if fallback_text:
                parts.append(fallback_text)

        return ArticleDocument(
            url=article_url,
            title=title,
            category=category,
            text="\n".join(parts),
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        selectors = [
            "h1.article-title",
            "h1",
            "title",
        ]
        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                return self._normalize_text(node.get_text(" ", strip=True))
        return "Untitled Article"

    def _extract_category(self, soup: BeautifulSoup) -> str:
        breadcrumb_items = soup.select("nav[aria-label='Breadcrumb'] li, .breadcrumbs li")
        if breadcrumb_items:
            texts = [
                self._normalize_text(item.get_text(" ", strip=True))
                for item in breadcrumb_items
                if item.get_text(strip=True)
            ]
            if texts:
                return " > ".join(texts)
        return "Atome Card"

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        candidate_selectors = [
            "article",
            ".article-body",
            ".article-content",
            "main",
            "[role='main']",
        ]

        container = None
        for selector in candidate_selectors:
            container = soup.select_one(selector)
            if container:
                break

        if container is None:
            container = soup.body or soup

        parts: List[str] = []

        for element in container.find_all(
            ["h1", "h2", "h3", "h4", "p", "li"]
        ):
            text = element.get_text(" ", strip=True)
            text = self._normalize_text(text)

            if not text:
                continue

            if len(text) < 2:
                continue

            parts.append(text)

        return "\n".join(parts)

    def _normalize_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = text.replace("\xa0", " ").strip()
        return text

    def _chunk_text(self, text: str) -> List[str]:
        if not text:
            return []

        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        chunks: List[str] = []
        current = ""

        for para in paragraphs:
            if not current:
                current = para
                continue

            if len(current) + 1 + len(para) <= settings.chunk_size:
                current += "\n" + para
            else:
                chunks.append(current)
                overlap = current[-settings.chunk_overlap :] if settings.chunk_overlap > 0 else ""
                current = overlap + "\n" + para if overlap else para

        if current:
            chunks.append(current)

        return [c.strip() for c in chunks if c.strip()]

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            model=settings.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def _make_chunk_id(self, url: str, chunk_index: int, text: str) -> str:
        raw = f"{url}:{chunk_index}:{text[:80]}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _has_existing_embeddings(self, source_url: str) -> bool:
        existing = self.collection.get(where={"source_url": source_url}, limit=1)
        return bool(existing.get("ids"))

    def _delete_existing_embeddings(self, source_url: str) -> None:
        self.collection.delete(where={"source_url": source_url})

    def _extract_locale_from_path(self, path: str) -> str:
        parts = [segment for segment in path.split("/") if segment]
        if len(parts) >= 2 and parts[0] == "hc":
            return parts[1]
        return ""

    def _extract_category_id_from_path(self, path: str) -> str:
        match = re.search(r"/categories/(\d+)", path)
        return match.group(1) if match else ""

    def _extract_article_id_from_path(self, path: str) -> str:
        match = re.search(r"/articles/(\d+)", path)
        return match.group(1) if match else ""