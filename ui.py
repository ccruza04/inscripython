"""Rendering and audio helpers for Inscripython."""

from __future__ import annotations

import math
from array import array
from dataclasses import dataclass, field

import pygame

from card import Card
from combat import AttackEvent, CombatSystem
from constants import (
    ACCENT_COLOR,
    BAD_COLOR,
    BG_COLOR,
    CARD_HEIGHT,
    CARD_WIDTH,
    ENEMY_ROW_Y,
    FIRST_SLOT_X,
    GOOD_COLOR,
    HAND_SPACING,
    HAND_Y,
    PANEL_COLOR,
    PLAYER_ROW_Y,
    SLOT_GAP,
    SOUND_SAMPLE_RATE,
    TEXT_COLOR,
)


class SoundManager:
    def __init__(self) -> None:
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            pygame.mixer.init(frequency=SOUND_SAMPLE_RATE, size=-16, channels=1)
            self.enabled = True
            self.sounds = {
                "place": self._tone(420, 0.08, 0.5),
                "sacrifice": self._tone(220, 0.12, 0.5),
                "attack": self._tone(640, 0.05, 0.4),
                "win": self._tone(800, 0.18, 0.5),
                "lose": self._tone(120, 0.2, 0.5),
            }
        except pygame.error:
            self.enabled = False

    def _tone(self, freq: float, duration: float, volume: float) -> pygame.mixer.Sound:
        length = int(SOUND_SAMPLE_RATE * duration)
        samples = array("h")
        for i in range(length):
            t = i / SOUND_SAMPLE_RATE
            env = max(0.0, 1 - (i / length))
            samples.append(int(math.sin(2 * math.pi * freq * t) * 32767 * volume * env))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name: str) -> None:
        if self.enabled and name in self.sounds:
            self.sounds[name].play()


@dataclass
class UIState:
    selected_hand: int | None = None
    selected_slot: int | None = None
    selected_sacrifices: set[int] = field(default_factory=set)


class GameUI:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font = pygame.font.SysFont("georgia", 22)
        self.small = pygame.font.SysFont("georgia", 18)
        self.big = pygame.font.SysFont("georgia", 36)

    def draw(self, combat: CombatSystem, ui: UIState, event_name: str, node_index: int, total_nodes: int) -> None:
        self.screen.fill(BG_COLOR)
        self._draw_table_panels()
        self._draw_slots(combat)
        self._draw_hand(combat, ui)
        self._draw_hud(combat, event_name, node_index, total_nodes)
        pygame.display.flip()

    def _draw_table_panels(self) -> None:
        pygame.draw.rect(self.screen, PANEL_COLOR, pygame.Rect(40, 80, 1200, 560), border_radius=14)

    def _draw_slots(self, combat: CombatSystem) -> None:
        for idx in range(4):
            x = FIRST_SLOT_X + idx * SLOT_GAP
            self._draw_card_placeholder(x, PLAYER_ROW_Y)
            self._draw_card_placeholder(x, ENEMY_ROW_Y)

            p_card = combat.board.player_slots[idx]
            e_card = combat.board.enemy_slots[idx]
            if p_card:
                self._draw_card(p_card, x, PLAYER_ROW_Y)
            if e_card:
                self._draw_card(e_card, x, ENEMY_ROW_Y)

        for event in combat.attack_events:
            self._draw_attack_line(event)

    def _draw_attack_line(self, event: AttackEvent) -> None:
        y_start = ENEMY_ROW_Y + CARD_HEIGHT // 2 if event.attacker_side == "enemy" else PLAYER_ROW_Y + CARD_HEIGHT // 2
        x_start = FIRST_SLOT_X + event.from_slot * SLOT_GAP + CARD_WIDTH // 2
        y_end = PLAYER_ROW_Y + CARD_HEIGHT // 2 if event.attacker_side == "enemy" else ENEMY_ROW_Y + CARD_HEIGHT // 2
        x_end = x_start if event.to_slot is None else FIRST_SLOT_X + event.to_slot * SLOT_GAP + CARD_WIDTH // 2
        pygame.draw.line(self.screen, ACCENT_COLOR, (x_start, y_start), (x_end, y_end), width=4)

    def _draw_card_placeholder(self, x: int, y: int) -> None:
        pygame.draw.rect(self.screen, (70, 60, 52), pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT), width=2, border_radius=9)

    def _draw_card(self, card: Card, x: int, y: int, selected: bool = False) -> None:
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        color = (121, 99, 74) if card.rarity == "rare" else (95, 79, 61)
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, (200, 170, 120) if selected else (40, 32, 26), rect, width=3, border_radius=8)

        title = self.small.render(card.name, True, TEXT_COLOR)
        self.screen.blit(title, (x + 8, y + 8))
        stats = self.font.render(f"{card.attack}/{card.health}", True, TEXT_COLOR)
        self.screen.blit(stats, (x + 8, y + CARD_HEIGHT - 34))
        cost = self.small.render(f"Sangre: {card.blood_cost}", True, BAD_COLOR)
        self.screen.blit(cost, (x + 8, y + CARD_HEIGHT - 58))
        if card.abilities:
            abilities = self.small.render(",".join(a[:3].upper() for a in card.abilities), True, GOOD_COLOR)
            self.screen.blit(abilities, (x + 8, y + CARD_HEIGHT - 82))

    def _draw_hand(self, combat: CombatSystem, ui: UIState) -> None:
        hand = combat.player.hand
        base_x = max(40, (1280 - len(hand) * HAND_SPACING) // 2)
        for i, card in enumerate(hand):
            x = base_x + i * HAND_SPACING
            y = HAND_Y - CARD_HEIGHT
            self._draw_card(card, x, y, selected=(ui.selected_hand == i))

    def _draw_hud(self, combat: CombatSystem, event_name: str, node_index: int, total_nodes: int) -> None:
        phase = self.font.render(f"Fase: {combat.phase.upper()} | Turno {combat.turn}", True, TEXT_COLOR)
        self.screen.blit(phase, (50, 25))
        balance = self.big.render(f"Balanza: {combat.balance}", True, GOOD_COLOR if combat.balance >= 0 else BAD_COLOR)
        self.screen.blit(balance, (520, 24))
        route = self.small.render(f"Mapa {node_index + 1}/{total_nodes} - Evento: {event_name}", True, TEXT_COLOR)
        self.screen.blit(route, (980 - route.get_width() // 2, 25))

        tips = self.small.render(
            "Click carta mano, click casilla para invocar; click tus cartas para sacrificio. [E] terminar fase [S] guardar [L] cargar",
            True,
            TEXT_COLOR,
        )
        self.screen.blit(tips, (70, 685))

        logs = combat.event_log[-4:]
        for i, msg in enumerate(logs):
            line = self.small.render(msg, True, TEXT_COLOR)
            self.screen.blit(line, (50, 560 + i * 22))

    def hand_index_from_pos(self, hand_count: int, pos: tuple[int, int]) -> int | None:
        base_x = max(40, (1280 - hand_count * HAND_SPACING) // 2)
        x, y = pos
        for i in range(hand_count):
            rect = pygame.Rect(base_x + i * HAND_SPACING, HAND_Y - CARD_HEIGHT, CARD_WIDTH, CARD_HEIGHT)
            if rect.collidepoint(x, y):
                return i
        return None

    def slot_index_from_pos(self, row_enemy: bool, pos: tuple[int, int]) -> int | None:
        y = ENEMY_ROW_Y if row_enemy else PLAYER_ROW_Y
        for i in range(4):
            rect = pygame.Rect(FIRST_SLOT_X + i * SLOT_GAP, y, CARD_WIDTH, CARD_HEIGHT)
            if rect.collidepoint(*pos):
                return i
        return None
