# hybrid/state.py

"""
State tracking for the hybrid recipe assistant.

We keep track of:
- the parsed recipe data (dict from the LLM parser)
- the current step index (0-based)
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class RecipeState:
    """Tracks the current step for a single recipe."""
    recipe: Dict[str, Any]
    current_step: Optional[int] = None  # 0-based index

    def has_steps(self) -> bool:
        return bool(self.recipe.get("steps"))

    def total_steps(self) -> int:
        return len(self.recipe.get("steps", []))

    def go_to_first(self) -> None:
        if self.has_steps():
            self.current_step = 0

    def go_to_step(self, idx: int) -> None:
        """Set current_step to a specific 0-based index, clamped to range."""
        if not self.has_steps():
            self.current_step = None
            return
        n = self.total_steps()
        self.current_step = max(0, min(idx, n - 1))

    def next_step(self) -> None:
        if not self.has_steps():
            return
        if self.current_step is None:
            self.current_step = 0
        elif self.current_step < self.total_steps() - 1:
            self.current_step += 1

    def prev_step(self) -> None:
        if not self.has_steps():
            return
        if self.current_step is None:
            self.current_step = 0
        elif self.current_step > 0:
            self.current_step -= 1

    def get_current_step_text(self) -> Optional[str]:
        if self.current_step is None:
            return None
        steps: List[str] = self.recipe.get("steps", [])
        if 0 <= self.current_step < len(steps):
            return steps[self.current_step]
        return None

    def build_step_context(self) -> Dict[str, Any]:
        """
        Build a small structured representation of the current step to send
        along with the QA prompt. We keep it simple: step number + text.
        """
        if self.current_step is None or not self.has_steps():
            return {
                "current_step": None,
                "description": None,
            }

        step_number = self.current_step + 1
        description = self.get_current_step_text()

        # You can enrich this later (e.g., infer tools, methods) if desired.
        return {
            "current_step": step_number,
            "description": description,
            "ingredients": [],   # left empty in hybrid version
            "tools": [],
            "methods": [],
            "time": {},
            "temperature": {},
        }
