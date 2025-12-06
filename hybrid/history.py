# hybrid/history.py

"""
Simple helper for storing conversation history as a list of (speaker, text) pairs.
"""

from typing import List, Tuple


class ConversationHistory:
    def __init__(self) -> None:
        self._messages: List[Tuple[str, str]] = []

    def add_user(self, text: str) -> None:
        self._messages.append(("User", text))

    def add_bot(self, text: str) -> None:
        self._messages.append(("Assistant", text))

    def as_list(self) -> List[Tuple[str, str]]:
        return list(self._messages)
