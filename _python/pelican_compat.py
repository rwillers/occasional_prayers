"""Compatibility helpers to ease Urubu -> Pelican migration."""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

from pelican import signals
from pelican.contents import Page
from pelican.generators import Generator, PagesGenerator
import yaml

SUPPORTED_LAYOUTS = {"home", "index", "page", "search", "tag"}
_FRONT_MATTER_CACHE: dict[str, dict[str, Any]] = {}


def _layout_value(page: Page) -> str:
    layout = str(page.metadata.get("layout", "page")).strip().lower()
    if layout in SUPPORTED_LAYOUTS:
        return layout
    return "page"


def _source_order(page: Page) -> int | None:
    value = page.metadata.get("source_order")
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _sort_key(page: Page) -> tuple[int, Any]:
    source_order = _source_order(page)
    if source_order is not None:
        return (0, source_order)
    return (1, page.title.lower())


def _normalize_content_refs(raw_value: Any) -> list[str]:
    if raw_value is None:
        return []
    if isinstance(raw_value, (list, tuple)):
        return [str(item).strip() for item in raw_value if str(item).strip()]
    if isinstance(raw_value, str):
        if not raw_value.strip():
            return []
        if "\n" in raw_value:
            return [line.strip() for line in raw_value.splitlines() if line.strip()]
        if "," in raw_value:
            return [item.strip() for item in raw_value.split(",") if item.strip()]
        return [raw_value.strip()]
    value = str(raw_value).strip()
    return [value] if value else []


def _normalize_tagline(raw_value: Any) -> str:
    if raw_value is None:
        return ""
    if isinstance(raw_value, (list, tuple)):
        parts = [str(item).strip() for item in raw_value if str(item).strip()]
        return " ".join(parts)
    return str(raw_value).strip()


def _normalize_title(raw_value: Any) -> str:
    if raw_value is None:
        return ""
    value = str(raw_value).strip()
    while len(value) >= 2 and value[0] in {"'", '"'} and value[-1] == value[0]:
        value = value[1:-1].strip()
    return value


def _clean_tag_token(value: str) -> str:
    cleaned = value.strip().strip("[]").strip()
    if (
        cleaned.startswith(("'", '"'))
        and cleaned.endswith(("'", '"'))
        and len(cleaned) >= 2
    ):
        cleaned = cleaned[1:-1]
    return cleaned.strip()


def _extract_tag_names(raw_value: Any) -> list[str]:
    if raw_value is None:
        return []
    if isinstance(raw_value, (list, tuple)):
        names: list[str] = []
        for item in raw_value:
            if isinstance(item, str):
                stripped = item.strip()
                if stripped.startswith("[") and stripped.endswith("]"):
                    names.extend(_extract_tag_names(stripped))
                    continue
                cleaned = _clean_tag_token(stripped)
                if cleaned:
                    names.append(cleaned)
                continue
            names.extend(_extract_tag_names(item))
        return names
    if not isinstance(raw_value, str):
        return _extract_tag_names(str(raw_value))

    value = raw_value.strip()
    if not value:
        return []

    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            parsed = None
        if isinstance(parsed, (list, tuple)):
            return [
                _clean_tag_token(str(item))
                for item in parsed
                if _clean_tag_token(str(item))
            ]

    if "," in value:
        return [
            _clean_tag_token(item)
            for item in value.split(",")
            if _clean_tag_token(item)
        ]

    cleaned = _clean_tag_token(value)
    return [cleaned] if cleaned else []


def _load_front_matter(source_path: str) -> dict[str, Any]:
    cached = _FRONT_MATTER_CACHE.get(source_path)
    if cached is not None:
        return cached

    path = Path(source_path)
    if not path.exists():
        _FRONT_MATTER_CACHE[source_path] = {}
        return {}

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        _FRONT_MATTER_CACHE[source_path] = {}
        return {}

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        _FRONT_MATTER_CACHE[source_path] = {}
        return {}

    raw_yaml = "\n".join(lines[1:end_index])
    try:
        parsed = yaml.safe_load(raw_yaml) or {}
    except yaml.YAMLError:
        parsed = {}
    metadata = parsed if isinstance(parsed, dict) else {}
    _FRONT_MATTER_CACHE[source_path] = metadata
    return metadata


def _tag_path_segment(tag_name: str) -> str:
    return tag_name.replace("/", "%2F")


def _public_url(content: Page) -> str:
    url = (getattr(content, "url", "") or "").lstrip("/")
    if not url:
        return "/"
    if url.endswith("index.html"):
        return f"/{url[:-10]}"
    return f"/{url}"


def set_template_from_layout(content: Any) -> None:
    if not isinstance(content, Page):
        return
    front_matter = _load_front_matter(content.source_path)
    normalized_title = _normalize_title(front_matter.get("title", content.title))
    if normalized_title:
        content.title = normalized_title
        content.metadata["title"] = normalized_title
    content.metadata["tagline"] = _normalize_tagline(
        front_matter.get("tagline", content.metadata.get("tagline"))
    )
    content.compat_tags = _extract_tag_names(
        front_matter.get("tags", content.metadata.get("tags"))
    )
    content.compat_tag_links = [
        {"name": tag_name, "segment": _tag_path_segment(tag_name)}
        for tag_name in content.compat_tags
    ]
    content.template = _layout_value(content)


def attach_compat_context(generators: list[Any]) -> None:
    pages: list[Page] = []
    for generator in generators:
        if isinstance(generator, PagesGenerator):
            pages.extend(generator.pages)
            pages.extend(generator.hidden_pages)

    section_index_pages: dict[str, Page] = {}
    directory_index_pages: dict[str, Page] = {}
    section_children: dict[str, list[Page]] = defaultdict(list)
    all_tag_names: set[str] = set()

    for page in pages:
        for tag_name in getattr(page, "compat_tags", []):
            all_tag_names.add(tag_name)
        if not getattr(page, "compat_tags", []):
            for tag in getattr(page, "tags", []) or []:
                all_tag_names.add(tag.name)

        relative_path = page.relative_source_path or page.source_path
        path = PurePosixPath(relative_path)
        if len(path.parts) < 2:
            continue

        section_name = path.parts[0]
        if path.name == "index.md":
            directory_key = str(path.parent)
            if directory_key and directory_key != ".":
                directory_index_pages[directory_key] = page
            section_index_pages[section_name] = page
            continue
        section_children[section_name].append(page)

    sorted_tag_names = sorted(all_tag_names, key=str.casefold)
    sorted_tags = [
        {"name": tag_name, "segment": _tag_path_segment(tag_name)}
        for tag_name in sorted_tag_names
    ]
    for page in pages:
        page.all_tag_links = sorted_tags

    for section, children in section_children.items():
        children.sort(key=_sort_key)
        index_page = section_index_pages.get(section)
        if index_page is not None:
            index_page.section_children = children

    section_sources: dict[str, dict[str, str]] = {}
    for section, index_page in section_index_pages.items():
        short_title = str(index_page.metadata.get("short_title", "")).strip()
        section_sources[section] = {
            "title": str(index_page.title).strip(),
            "short_title": short_title,
        }

    for page in pages:
        url_path = PurePosixPath((getattr(page, "url", "") or "").lstrip("/"))
        if len(url_path.parts) < 2:
            page.compat_section_sources = section_sources
            continue

        section_key = url_path.parts[0]
        source_info = section_sources.get(section_key)
        if source_info is None:
            page.compat_section_sources = section_sources
            continue

        page.compat_section_title = source_info["title"]
        page.compat_section_short_title = source_info["short_title"]
        page.compat_section_sources = section_sources

    for page in pages:
        if _layout_value(page) != "page":
            continue

        relative_path = page.relative_source_path or page.source_path
        path = PurePosixPath(relative_path)
        if len(path.parts) < 2:
            page.compat_breadcrumbs = [{"title": page.title, "url": _public_url(page)}]
            continue

        breadcrumbs: list[dict[str, str]] = []
        for depth in range(1, len(path.parts)):
            directory_key = "/".join(path.parts[:depth])
            index_page = directory_index_pages.get(directory_key)
            if index_page is None:
                continue
            breadcrumbs.append(
                {"title": index_page.title, "url": _public_url(index_page)}
            )
        breadcrumbs.append({"title": page.title, "url": _public_url(page)})

        if len(breadcrumbs) > 1:
            page.compat_breadcrumbs = breadcrumbs

    home_page = next((page for page in pages if _layout_value(page) == "home"), None)
    if home_page is None:
        return

    home_front_matter = _load_front_matter(home_page.source_path)
    home_refs = _normalize_content_refs(
        home_front_matter.get(
            "section_refs",
            home_front_matter.get(
                "content",
                home_page.metadata.get(
                    "section_refs", home_page.metadata.get("content")
                ),
            ),
        )
    )
    section_links: list[Page] = []
    for ref in home_refs:
        section_key = ref.strip().lstrip("/").rstrip("/")
        section_page = section_index_pages.get(section_key)
        if section_page is not None:
            section_links.append(section_page)
    if not section_links:
        section_links = sorted(section_index_pages.values(), key=_sort_key)
    home_page.section_links = section_links


class CompatTagPagesGenerator(Generator):
    """Generate tag detail pages for page content."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.tag_pages: list[dict[str, Any]] = []
        super().__init__(*args, **kwargs)

    def generate_context(self) -> None:
        pages: list[Page] = list(self.context.get("pages", []))
        pages.extend(self.context.get("hidden_pages", []))

        tag_to_pages: dict[str, list[Page]] = defaultdict(list)
        for page in pages:
            for tag_name in getattr(page, "compat_tags", []):
                tag_to_pages[tag_name].append(page)

        tag_pages: list[dict[str, Any]] = []
        for tag_name in sorted(tag_to_pages, key=str.casefold):
            tagged_pages = sorted(tag_to_pages[tag_name], key=_sort_key)
            segment = _tag_path_segment(tag_name)
            tag_pages.append(
                {
                    "name": tag_name,
                    "segment": segment,
                    "url": f"tag/{segment}/",
                    "save_as": f"tag/{segment}/index.html",
                    "pages": tagged_pages,
                }
            )
        self.tag_pages = tag_pages

    def generate_output(self, writer: Any) -> None:
        template = self.get_template("tag_detail")
        for tag_page in self.tag_pages:
            writer.write_file(
                tag_page["save_as"],
                template,
                self.context,
                relative_urls=self.settings["RELATIVE_URLS"],
                override_output=False,
                url=tag_page["url"],
                tag_name=tag_page["name"],
                tagged_pages=tag_page["pages"],
            )


def get_generators(_pelican_obj: Any) -> type[CompatTagPagesGenerator]:
    return CompatTagPagesGenerator


def register() -> None:
    signals.content_object_init.connect(set_template_from_layout)
    signals.all_generators_finalized.connect(attach_compat_context)
    signals.get_generators.connect(get_generators)
