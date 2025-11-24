

"""
Typed protocol definitions for the JSON 'recipe' structure used between
the Vue SPA and the backend.

These are purely for type-checking / documentation and do not affect runtime.
"""

from __future__ import annotations

from typing import List, Optional, TypedDict


class RuleOptions(TypedDict, total=False):
    value: str
    delimiter: str
    separateNodes: bool
    rootOnly: bool
    excludeKeys: List[str]


class Rule(TypedDict, total=False):
    id: str
    column: str
    operation: str
    options: RuleOptions
    enabled: bool


class Insights(TypedDict, total=False):
    sources: List[str]
    targets: List[str]
    threshold: float


class Recipe(TypedDict, total=False):
    rules: List[Rule]
    insights: Insights