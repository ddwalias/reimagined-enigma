"""Backend-only data models."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Citation:
    title: str
    url: str
    document_name: str
