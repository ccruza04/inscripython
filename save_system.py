"""JSON save/load management."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from constants import SAVE_FILE


@dataclass
class SaveState:
    player_deck: list[str]
    progress_node: int
    victories: int
    losses: int


def default_state() -> SaveState:
    return SaveState(player_deck=[], progress_node=0, victories=0, losses=0)


def save_game(state: SaveState, path: Path = SAVE_FILE) -> None:
    payload = {
        "player_deck": state.player_deck,
        "progress_node": state.progress_node,
        "victories": state.victories,
        "losses": state.losses,
    }
    temp_path = path.with_suffix(".tmp")
    with temp_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    temp_path.replace(path)


def load_game(path: Path = SAVE_FILE) -> SaveState:
    if not path.exists():
        return default_state()
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return SaveState(
            player_deck=list(data.get("player_deck", [])),
            progress_node=int(data.get("progress_node", 0)),
            victories=int(data.get("victories", 0)),
            losses=int(data.get("losses", 0)),
        )
    except (json.JSONDecodeError, OSError, ValueError, TypeError):
        return default_state()
