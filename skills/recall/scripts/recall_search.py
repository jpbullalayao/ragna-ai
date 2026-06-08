#!/usr/bin/env python3
"""Search and display prior agent session transcripts across harnesses."""

from __future__ import annotations

import argparse
import glob
import hashlib
import html
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "i",
        "we",
        "you",
        "they",
        "he",
        "she",
        "my",
        "our",
        "your",
        "their",
        "about",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "under",
        "over",
        "what",
        "which",
        "who",
        "whom",
        "how",
        "when",
        "where",
        "why",
    }
)

MAX_FILES_SCANNED = 2000
TITLE_MAX = 120
SNIPPET_MAX = 200
TOOL_TYPES = frozenset(
    {
        "tool_use",
        "tool_result",
        "tool_call",
        "function_call",
        "function_call_output",
        "tool_call_output",
        "image",
        "image_url",
    }
)


@dataclass(frozen=True)
class Harness:
    name: str
    globs: tuple[str, ...]
    file_kind: str  # "jsonl" | "json"
    project_match: str  # dir-slug | line-cwd | meta-cwd | gemini-hash


def home() -> Path:
    return Path.home()


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", home() / ".codex"))


HARNESSES: tuple[Harness, ...] = (
    Harness(
        name="cursor",
        globs=(str(home() / ".cursor" / "projects" / "*" / "agent-transcripts" / "**" / "*.jsonl"),),
        file_kind="jsonl",
        project_match="dir-slug",
    ),
    Harness(
        name="claude",
        globs=(str(home() / ".claude" / "projects" / "*" / "*.jsonl"),),
        file_kind="jsonl",
        project_match="line-cwd",
    ),
    Harness(
        name="codex",
        globs=(str(codex_home() / "sessions" / "*" / "*" / "*" / "rollout-*.jsonl"),),
        file_kind="jsonl",
        project_match="meta-cwd",
    ),
    Harness(
        name="gemini",
        globs=(
            str(home() / ".gemini" / "tmp" / "*" / "chats" / "*.json"),
            str(home() / ".gemini" / "tmp" / "*" / "logs.json"),
        ),
        file_kind="json",
        project_match="gemini-hash",
    ),
)


def normalize_path(path: str | Path) -> str:
    return os.path.normpath(os.path.abspath(str(path)))


def slugify_path(path: str) -> str:
    normalized = normalize_path(path)
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return slug


def cursor_slug(path: str) -> str:
    normalized = normalize_path(path).lstrip(os.sep)
    return re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()


def claude_slug(path: str) -> str:
    normalized = normalize_path(path)
    return re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()


def git_root(start: str | Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(start),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            return normalize_path(result.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def gemini_hashes(cwd: str) -> set[str]:
    candidates = {normalize_path(cwd)}
    root = git_root(cwd)
    if root:
        candidates.add(root)
    hashes: set[str] = set()
    for candidate in candidates:
        for variant in (candidate, candidate.rstrip(os.sep), candidate + os.sep):
            digest = hashlib.sha256(variant.encode("utf-8")).hexdigest()
            hashes.add(digest)
    return hashes


def tokenize_query(query: str) -> list[str]:
    terms = re.findall(r"[a-zA-Z0-9_./-]+", query.lower())
    return [t for t in terms if len(t) > 1 and t not in STOPWORDS]


def score_text(text_lower: str, terms: list[str]) -> int:
    if not terms:
        return 0
    return sum(text_lower.count(term) for term in terms)


def read_raw_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def expand_globs(patterns: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        root = pattern.split("*", 1)[0]
        if root and not os.path.exists(root):
            continue
        matches = glob.glob(pattern, recursive=True)
        files.extend(Path(match) for match in matches if os.path.isfile(match))
    return files


def harness_for_path(path: Path) -> Harness | None:
    path_str = str(path)
    if "/.cursor/projects/" in path_str and path.suffix == ".jsonl":
        return next(h for h in HARNESSES if h.name == "cursor")
    if "/.claude/projects/" in path_str and path.suffix == ".jsonl":
        return next(h for h in HARNESSES if h.name == "claude")
    if "/sessions/" in path_str and path.name.startswith("rollout-") and path.suffix == ".jsonl":
        return next(h for h in HARNESSES if h.name == "codex")
    if "/.gemini/tmp/" in path_str and path.suffix == ".json":
        return next(h for h in HARNESSES if h.name == "gemini")
    return None


def extract_cwd_from_jsonl(path: Path, strategy: str) -> str | None:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cwd = obj.get("cwd")
                if isinstance(cwd, str) and cwd:
                    return normalize_path(cwd)
                if strategy == "meta-cwd":
                    payload = obj.get("payload") or obj.get("session") or obj
                    if isinstance(payload, dict):
                        for key in ("cwd", "working_directory", "workingDirectory"):
                            value = payload.get(key)
                            if isinstance(value, str) and value:
                                return normalize_path(value)
                break
    except OSError:
        return None
    return None


def project_dir_slug(path: Path, harness: Harness) -> str | None:
    parts = path.parts
    if harness.name == "cursor" and ".cursor" in parts and "projects" in parts:
        idx = parts.index("projects")
        if idx + 1 < len(parts):
            return parts[idx + 1].lower()
    if harness.name == "claude" and ".claude" in parts and "projects" in parts:
        idx = parts.index("projects")
        if idx + 1 < len(parts):
            return parts[idx + 1].lower()
    return None


def matches_project(path: Path, harness: Harness, cwd: str, all_projects: bool) -> bool:
    if all_projects:
        return True

    cwd_norm = normalize_path(cwd)
    cwd_slug = slugify_path(cwd_norm)
    cursor_cwd_slug = cursor_slug(cwd_norm)
    claude_cwd_slug = claude_slug(cwd_norm)

    if harness.project_match == "dir-slug":
        dir_slug = project_dir_slug(path, harness)
        if not dir_slug:
            return False
        if harness.name == "cursor":
            return dir_slug == cursor_cwd_slug
        return dir_slug == cwd_slug or dir_slug == claude_cwd_slug

    if harness.project_match == "line-cwd":
        line_cwd = extract_cwd_from_jsonl(path, "line-cwd")
        if line_cwd:
            return line_cwd == cwd_norm
        dir_slug = project_dir_slug(path, harness)
        return bool(dir_slug and (dir_slug == cwd_slug or dir_slug == claude_cwd_slug))

    if harness.project_match == "meta-cwd":
        meta_cwd = extract_cwd_from_jsonl(path, "meta-cwd")
        if meta_cwd:
            return meta_cwd == cwd_norm
        return True

    if harness.project_match == "gemini-hash":
        parts = path.parts
        if ".gemini" not in parts or "tmp" not in parts:
            return False
        idx = parts.index("tmp")
        if idx + 1 >= len(parts):
            return False
        project_hash = parts[idx + 1]
        hashes = gemini_hashes(cwd_norm)
        if project_hash in hashes:
            return True
        return False

    return True


def session_id_from_path(path: Path, harness: Harness | None) -> str:
    if harness and harness.name == "codex":
        match = re.search(
            r"rollout-[\d-]+T[\d-]+-([a-f0-9-]+)\.jsonl$",
            path.name,
            re.IGNORECASE,
        )
        if match:
            return match.group(1)
    stem = path.stem
    if re.fullmatch(r"[a-f0-9-]{8,}", stem, re.IGNORECASE):
        return stem
    return stem


def strip_markup(text: str) -> str:
    text = re.sub(r"<user_query>\s*", "", text)
    text = re.sub(r"</user_query>\s*", "", text)
    text = re.sub(r"<timestamp>.*?</timestamp>\s*", "", text, flags=re.DOTALL)
    text = re.sub(r"<command-message>.*?</command-message>\s*", "", text, flags=re.DOTALL)
    text = re.sub(r"<command-name>.*?</command-name>\s*", "", text, flags=re.DOTALL)
    text = html.unescape(text)
    return text.strip()


def collect_text(value: Any) -> list[str]:
    texts: list[str] = []
    if value is None:
        return texts
    if isinstance(value, str):
        cleaned = strip_markup(value)
        if cleaned:
            texts.append(cleaned)
        return texts
    if isinstance(value, list):
        for item in value:
            texts.extend(collect_text(item))
        return texts
    if isinstance(value, dict):
        item_type = str(value.get("type", "")).lower()
        if item_type in TOOL_TYPES:
            return texts
        if "text" in value and isinstance(value["text"], str):
            cleaned = strip_markup(value["text"])
            if cleaned:
                texts.append(cleaned)
            return texts
        if "content" in value:
            texts.extend(collect_text(value["content"]))
        if "parts" in value:
            texts.extend(collect_text(value["parts"]))
        if "message" in value:
            texts.extend(collect_text(value["message"]))
        return texts
    return texts


def role_from_record(record: dict[str, Any]) -> str | None:
    for key in ("role", "type"):
        value = record.get(key)
        if isinstance(value, str):
            lowered = value.lower()
            if lowered in {"user", "human"}:
                return "user"
            if lowered in {"assistant", "model", "agent", "ai"}:
                return "assistant"
    message = record.get("message")
    if isinstance(message, dict):
        role = message.get("role")
        if isinstance(role, str):
            lowered = role.lower()
            if lowered in {"user", "human"}:
                return "user"
            if lowered in {"assistant", "model", "agent", "ai"}:
                return "assistant"
    return None


def text_from_record(record: dict[str, Any]) -> str:
    chunks: list[str] = []
    for key in ("message", "content", "parts"):
        if key in record:
            chunks.extend(collect_text(record[key]))
    if not chunks and "text" in record:
        chunks.extend(collect_text(record["text"]))
    return "\n".join(part for part in chunks if part).strip()


def timestamp_from_record(record: dict[str, Any]) -> str | None:
    for key in ("timestamp", "createdAt", "created_at", "time"):
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    return None


@dataclass
class Turn:
    role: str
    text: str
    timestamp: str | None = None


def iter_jsonl_records(path: Path) -> Iterator[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, dict):
                    yield obj
    except OSError:
        return


def iter_json_records(path: Path) -> Iterator[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return

    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                yield item
        return

    if isinstance(payload, dict):
        for key in ("messages", "history", "conversation", "entries", "logs"):
            value = payload.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        yield item
                return
        yield payload


def load_turns(path: Path) -> list[Turn]:
    harness = harness_for_path(path)
    iterator: Iterator[dict[str, Any]]
    if harness and harness.file_kind == "json":
        iterator = iter_json_records(path)
    elif path.suffix == ".json":
        iterator = iter_json_records(path)
    else:
        iterator = iter_jsonl_records(path)

    turns: list[Turn] = []
    for record in iterator:
        role = role_from_record(record)
        text = text_from_record(record)
        if not role or not text:
            continue
        turns.append(
            Turn(
                role=role,
                text=text,
                timestamp=timestamp_from_record(record),
            )
        )
    return turns


def first_user_title(path: Path) -> str:
    for turn in load_turns(path):
        if turn.role == "user":
            title = re.sub(r"\s+", " ", turn.text).strip()
            if title:
                return title[:TITLE_MAX]
    return path.name


def snippet_around_terms(text: str, terms: list[str]) -> str:
    lowered = text.lower()
    for term in terms:
        idx = lowered.find(term)
        if idx >= 0:
            start = max(0, idx - 60)
            end = min(len(text), idx + len(term) + 140)
            snippet = text[start:end].replace("\n", " ")
            snippet = re.sub(r"\s+", " ", snippet).strip()
            if start > 0:
                snippet = "..." + snippet
            if end < len(text):
                snippet = snippet + "..."
            return snippet[:SNIPPET_MAX]
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[:SNIPPET_MAX]


def collect_candidate_files(
    harnesses: Iterable[Harness],
    cwd: str,
    all_projects: bool,
    harness_filter: str | None,
) -> list[tuple[Harness, Path]]:
    candidates: list[tuple[Harness, Path]] = []
    seen: set[str] = set()

    for harness in harnesses:
        if harness_filter and harness.name != harness_filter:
            continue
        for path in expand_globs(harness.globs):
            key = str(path)
            if key in seen:
                continue
            seen.add(key)
            if matches_project(path, harness, cwd, all_projects):
                candidates.append((harness, path))
            if len(candidates) >= MAX_FILES_SCANNED:
                return candidates
    return candidates


def search_sessions(
    query: str,
    cwd: str,
    limit: int,
    all_projects: bool,
    harness_filter: str | None,
) -> list[dict[str, Any]]:
    terms = tokenize_query(query)
    results: list[dict[str, Any]] = []

    for harness, path in collect_candidate_files(HARNESSES, cwd, all_projects, harness_filter):
        raw = read_raw_text(path)
        if not raw:
            continue
        score = score_text(raw.lower(), terms)
        if score <= 0 and terms:
            continue

        turns = load_turns(path)
        snippets: list[str] = []
        for turn in turns:
            if turn.role == "user" and terms:
                snippet = snippet_around_terms(turn.text, terms)
                if snippet and snippet not in snippets:
                    snippets.append(snippet)
            if len(snippets) >= 2:
                break
        if not snippets and turns:
            snippets.append(snippet_around_terms(turns[0].text, terms))

        timestamps = [turn.timestamp for turn in turns if turn.timestamp]
        results.append(
            {
                "harness": harness.name,
                "path": str(path),
                "sessionId": session_id_from_path(path, harness),
                "title": first_user_title(path),
                "firstTs": timestamps[0] if timestamps else None,
                "lastTs": timestamps[-1] if timestamps else None,
                "score": score,
                "snippets": snippets,
            }
        )

    results.sort(key=lambda item: (-item["score"], item["lastTs"] or "", item["path"]))
    return results[:limit]


def filter_turns(turns: list[Turn], query: str | None, context: int) -> list[Turn]:
    if not query:
        return turns
    terms = tokenize_query(query)
    if not terms:
        return turns

    matched_indexes: set[int] = set()
    for idx, turn in enumerate(turns):
        lowered = turn.text.lower()
        if any(term in lowered for term in terms):
            matched_indexes.add(idx)

    if not matched_indexes:
        return turns

    selected: set[int] = set()
    for idx in matched_indexes:
        start = max(0, idx - context)
        end = min(len(turns), idx + context + 1)
        selected.update(range(start, end))
    return [turns[i] for i in sorted(selected)]


def format_turns(turns: list[Turn]) -> str:
    lines: list[str] = []
    for turn in turns:
        label = "USER" if turn.role == "user" else "ASSISTANT"
        if turn.timestamp:
            lines.append(f"[{turn.timestamp}] {label}:")
        else:
            lines.append(f"{label}:")
        lines.append(turn.text)
        lines.append("")
    return "\n".join(lines).strip()


def cmd_search(args: argparse.Namespace) -> int:
    cwd = normalize_path(args.cwd or os.getcwd())
    results = search_sessions(
        query=args.query,
        cwd=cwd,
        limit=args.limit,
        all_projects=args.all_projects,
        harness_filter=args.harness,
    )
    print(json.dumps(results, indent=2))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 1
    turns = load_turns(path)
    if not turns:
        print("No conversation turns found.", file=sys.stderr)
        return 1
    filtered = filter_turns(turns, args.query, args.context)
    print(format_turns(filtered))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Search prior sessions for a query")
    search_parser.add_argument("query", help="Topic or keywords to recall")
    search_parser.add_argument("--limit", type=int, default=5, help="Max sessions to return")
    search_parser.add_argument(
        "--all-projects",
        action="store_true",
        help="Search across all projects, not just the current cwd",
    )
    search_parser.add_argument(
        "--harness",
        choices=[h.name for h in HARNESSES],
        help="Limit search to one harness",
    )
    search_parser.add_argument(
        "--cwd",
        default=None,
        help="Project directory to scope search (defaults to current working directory)",
    )
    search_parser.set_defaults(func=cmd_search)

    show_parser = subparsers.add_parser("show", help="Show a cleaned transcript")
    show_parser.add_argument("path", help="Path to a transcript file")
    show_parser.add_argument("--query", default=None, help="Filter turns matching this query")
    show_parser.add_argument(
        "--context",
        type=int,
        default=1,
        help="Number of turns of context around each match",
    )
    show_parser.set_defaults(func=cmd_show)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
