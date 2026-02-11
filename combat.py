"""Turn based combat state machine."""

from __future__ import annotations

from dataclasses import dataclass, field

from board import Board
from card import Card
from constants import PHASE_ATTACK, PHASE_DRAW, PHASE_ENEMY, PHASE_PLAY, WIN_BALANCE
from enemy import EnemyAI
from player import Player


@dataclass
class AttackEvent:
    attacker_side: str
    from_slot: int
    to_slot: int | None
    damage: int


@dataclass
class CombatSystem:
    player: Player
    enemy: Player
    board: Board = field(default_factory=Board)
    ai: EnemyAI = field(default_factory=EnemyAI)
    phase: str = PHASE_DRAW
    balance: int = 0
    turn: int = 1
    battle_over: bool = False
    winner: str | None = None
    event_log: list[str] = field(default_factory=list)
    attack_events: list[AttackEvent] = field(default_factory=list)

    def start_battle(self) -> None:
        for _ in range(3):
            self.player.draw_card()
            self.enemy.draw_card()
        self.phase = PHASE_DRAW
        self.balance = 0
        self.turn = 1
        self.battle_over = False
        self.winner = None
        self.event_log = ["Comienza el combate."]

    def can_play_card(self, hand_index: int, sacrifices: list[int], slot_index: int) -> tuple[bool, str]:
        if self.phase != PHASE_PLAY:
            return False, "No es fase de invocación"
        if not (0 <= hand_index < len(self.player.hand)):
            return False, "Carta inválida"
        if not (0 <= slot_index < len(self.board.player_slots)):
            return False, "Posición inválida"
        if self.board.player_slots[slot_index] is not None:
            return False, "La posición está ocupada"

        card = self.player.hand[hand_index]
        if card.blood_cost == 0:
            return True, ""
        unique_sacrifices = sorted(set(sacrifices))
        if len(unique_sacrifices) < card.blood_cost:
            return False, "No hay sangre suficiente"
        for idx in unique_sacrifices:
            if idx < 0 or idx >= len(self.board.player_slots):
                return False, "Sacrificio inválido"
            if self.board.player_slots[idx] is None:
                return False, "Debes seleccionar cartas vivas para sacrificar"
            if idx == slot_index:
                return False, "No puedes sacrificar la misma casilla de invocación"
        return True, ""

    def play_player_card(self, hand_index: int, sacrifices: list[int], slot_index: int) -> tuple[bool, str]:
        valid, msg = self.can_play_card(hand_index, sacrifices, slot_index)
        if not valid:
            return False, msg

        card = self.player.remove_from_hand(hand_index)
        unique_sacrifices = sorted(set(sacrifices))
        for idx in unique_sacrifices[: card.blood_cost]:
            sacrificed = self.board.remove_card(enemy=False, index=idx)
            if sacrificed:
                self.event_log.append(f"Sacrificas a {sacrificed.name}.")

        self.board.place_card(enemy=False, index=slot_index, card=card)
        self.event_log.append(f"Invocas {card.name} en casilla {slot_index + 1}.")
        return True, ""

    def advance_phase(self) -> None:
        if self.battle_over:
            return
        if self.phase == PHASE_DRAW:
            self.player.draw_card()
            self.phase = PHASE_PLAY
            self.event_log.append("Robas una carta.")
        elif self.phase == PHASE_PLAY:
            self.phase = PHASE_ATTACK
            self.resolve_attacks(attacker_is_enemy=False)
            self._check_win()
            if not self.battle_over:
                self.phase = PHASE_ENEMY
                self.enemy_turn()
        elif self.phase == PHASE_ENEMY:
            self.turn += 1
            self.phase = PHASE_DRAW

    def enemy_turn(self) -> None:
        self.enemy.draw_card()
        play = self.ai.choose_play(self.enemy, self.board)
        if play:
            hand_idx, slot_idx, sacrifices = play
            card = self.enemy.remove_from_hand(hand_idx)
            for idx in sorted(sacrifices, reverse=True):
                sacrificed = self.board.remove_card(enemy=True, index=idx)
                if sacrificed:
                    self.event_log.append(f"El enemigo sacrifica a {sacrificed.name}.")
            self.board.place_card(enemy=True, index=slot_idx, card=card)
            self.event_log.append(f"El enemigo invoca {card.name}.")
        self.resolve_attacks(attacker_is_enemy=True)
        self._check_win()

    def resolve_attacks(self, attacker_is_enemy: bool) -> None:
        self.attack_events.clear()
        attackers = self.board.enemy_slots if attacker_is_enemy else self.board.player_slots
        defenders = self.board.player_slots if attacker_is_enemy else self.board.enemy_slots

        for slot, card in enumerate(list(attackers)):
            if card is None:
                continue
            for target_slot in self._attack_targets(slot, card):
                if target_slot < 0 or target_slot >= len(defenders):
                    continue
                defender = defenders[target_slot]
                power = self._effective_attack(card, attackers)
                if power <= 0:
                    continue
                if defender is None or (card.has_ability("flying") and not (defender and defender.has_ability("reach"))):
                    self.balance += (-power if attacker_is_enemy else power)
                    self.attack_events.append(AttackEvent("enemy" if attacker_is_enemy else "player", slot, None, power))
                    self.event_log.append(("El enemigo" if attacker_is_enemy else card.name) + f" hace {power} daño directo.")
                else:
                    dead = defender.take_damage(power)
                    self.attack_events.append(AttackEvent("enemy" if attacker_is_enemy else "player", slot, target_slot, power))
                    self.event_log.append(f"{card.name} golpea a {defender.name} por {power}.")
                    if card.has_ability("deathtouch"):
                        dead = True
                    if dead:
                        defenders[target_slot] = None
                        self.event_log.append(f"{defender.name} muere.")

    def _attack_targets(self, slot: int, card: Card) -> list[int]:
        if card.has_ability("tri_strike"):
            return [slot - 1, slot, slot + 1]
        if card.has_ability("split_strike"):
            return [slot - 1, slot + 1]
        return [slot]

    def _effective_attack(self, card: Card, friendly_slots: list[Card | None]) -> int:
        buff = 0
        idx = friendly_slots.index(card)
        for check in (idx - 1, idx + 1):
            if 0 <= check < len(friendly_slots):
                ally = friendly_slots[check]
                if ally and ally.has_ability("leader"):
                    buff += 1
        if card.has_ability("swarm"):
            ants = sum(1 for c in friendly_slots if c and c.name.endswith("Ant Worker"))
            return max(card.attack, ants)
        return card.attack + buff

    def _check_win(self) -> None:
        if self.balance >= WIN_BALANCE:
            self.battle_over = True
            self.winner = "player"
            self.event_log.append("¡Victoria!")
        elif self.balance <= -WIN_BALANCE:
            self.battle_over = True
            self.winner = "enemy"
            self.event_log.append("Has sido derrotado.")
