"""Shared paths, logging, and small I/O helpers for the replication package."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]


def project_path(*parts: str) -> Path:
    return ROOT.joinpath(*parts)


def ensure_directories() -> None:
    for relative in (
        "data/raw",
        "data/interim",
        "data/processed",
        "output/tables",
        "output/figures",
        "output/logs",
    ):
        project_path(relative).mkdir(parents=True, exist_ok=True)


def configure_logging(name: str) -> logging.Logger:
    ensure_directories()
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    file_handler = logging.FileHandler(project_path("output", "logs", f"{name}.log"))
    file_handler.setFormatter(formatter)
    logger.addHandler(stream)
    logger.addHandler(file_handler)
    return logger


def sha256(path: Path, block_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(block_size):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def existing(names: Iterable[str], available: Iterable[str]) -> list[str]:
    available_set = set(available)
    return [name for name in names if name in available_set]
