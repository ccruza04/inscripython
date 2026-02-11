"""Enemy AI behavior."""

from __future__ import annotations

from dataclasses import dataclass

from board import Board
from card import Card
from player import Player


@dataclass
class EnemyAI:
    """Decision making for enemy summoning."""

    def choose_play(self, enemy: Player, board: Board) -> tuple[int, int, list[int]] | None:
        """Returns (hand_index, slot_index, sacrifice_slots) or None."""
        open_slot = board.first_open_slot(enemy=True)
        if open_slot is None:
            return None

        candidates: list[tuple[int, int]] = []
        for idx, card in enumerate(enemy.hand):
            if card.blood_cost <= board.living_count(enemy=True):
                candidates.append((idx, self._summon_priority(card, open_slot, board)))
            elif card.blood_cost == 0:
                candidates.append((idx, self._summon_priority(card, open_slot, board)))

        if not candidates:
            return None

        hand_index = max(candidates, key=lambda c: c[1])[0]
        chosen = enemy.hand[hand_index]
        needed = chosen.blood_cost
        sacrifices: list[int] = []
        if needed > 0:
            values = []
            for i, c in enumerate(board.enemy_slots):
                if c is not None:
                    threat = c.attack + c.health
                    values.append((i, threat))
            values.sort(key=lambda v: v[1])
            sacrifices = [i for i, _ in values[:needed]]
            if len(sacrifices) < needed:
                return None

        slot_index = self._best_slot_for_attack(board, chosen)
        return hand_index, slot_index, sacrifices

    def _best_slot_for_attack(self, board: Board, card: Card) -> int:
        best_slot = board.first_open_slot(enemy=True)
        if best_slot is None:
            return 0
        best_score = -999
        for idx, occupant in enumerate(board.enemy_slots):
            if occupant is not None:
                continue
            target = board.player_slots[idx]
            score = 0
            if target is None:
                score += 6
            else:
                if card.attack >= target.health:
                    score += 8
                score += max(0, card.attack - target.attack)
            if score > best_score:
                best_score = score
                best_slot = idx
        return best_slot

    def _summon_priority(self, card: Card, slot: int, board: Board) -> int:
        target = board.player_slots[slot]
        priority = card.attack * 3 + card.health
        if target is None:
            priority += 4
        else:
            if card.attack >= target.health:
                priority += 5
        if "flying" in card.abilities:
            priority += 2
        return priority
