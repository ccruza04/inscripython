"""Board state and combat slot helpers."""

from __future__ import annotations

from dataclasses import dataclass, field

from constants import BOARD_SLOTS
from card import Card


@dataclass
class Board:
    player_slots: list[Card | None] = field(default_factory=lambda: [None] * BOARD_SLOTS)
    enemy_slots: list[Card | None] = field(default_factory=lambda: [None] * BOARD_SLOTS)

    def first_open_slot(self, enemy: bool) -> int | None:
        slots = self.enemy_slots if enemy else self.player_slots
        for i, card in enumerate(slots):
            if card is None:
                return i
        return None

    def place_card(self, enemy: bool, index: int, card: Card) -> bool:
        slots = self.enemy_slots if enemy else self.player_slots
        if index < 0 or index >= BOARD_SLOTS:
            return False
        if slots[index] is not None:
            return False
        slots[index] = card
        return True

    def remove_card(self, enemy: bool, index: int) -> Card | None:
        slots = self.enemy_slots if enemy else self.player_slots
        card = slots[index]
        slots[index] = None
        return card

    def living_count(self, enemy: bool) -> int:
        slots = self.enemy_slots if enemy else self.player_slots
        return sum(1 for c in slots if c is not None)
