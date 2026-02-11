"""Main game orchestration and state progression."""

from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

from card import card_from_name, cards_by_rarity
from combat import CombatSystem
from constants import EVENT_BOSS, EVENT_COMBAT, EVENT_RARE, EVENT_UPGRADE, FPS, PHASE_DRAW, SCREEN_HEIGHT, SCREEN_WIDTH
from deck import Deck, make_enemy_deck, make_starter_deck
from player import Player
from save_system import SaveState, load_game, save_game
from ui import GameUI, SoundManager, UIState


@dataclass
class MapNode:
    event: str


class EventMap:
    def __init__(self) -> None:
        self.nodes = self._generate()

    def _generate(self) -> list[MapNode]:
        mid = [random.choice([EVENT_COMBAT, EVENT_UPGRADE, EVENT_RARE]) for _ in range(5)]
        return [MapNode(EVENT_COMBAT), *[MapNode(e) for e in mid], MapNode(EVENT_BOSS)]


class InscripythonGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Inscripython")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.ui = GameUI(self.screen)
        self.sounds = SoundManager()
        self.ui_state = UIState()
        self.running = True

        self.map = EventMap()
        self.node_index = 0
        self.victories = 0
        self.losses = 0

        player = Player("Jugador", make_starter_deck())
        enemy = Player("Leshy", make_enemy_deck())
        self.combat = CombatSystem(player=player, enemy=enemy)
        self.combat.start_battle()

    def run(self) -> None:
        while self.running:
            self._handle_events()
            if self.combat.phase == PHASE_DRAW and not self.combat.battle_over:
                self.combat.advance_phase()
            self.ui.draw(
                self.combat,
                self.ui_state,
                self.current_event,
                self.node_index,
                len(self.map.nodes),
            )
            self.clock.tick(FPS)

    @property
    def current_event(self) -> str:
        return self.map.nodes[self.node_index].event

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    self.combat.advance_phase()
                    if self.combat.attack_events:
                        self.sounds.play("attack")
                    if self.combat.battle_over:
                        self.sounds.play("win" if self.combat.winner == "player" else "lose")
                        self._resolve_battle_end()
                elif event.key == pygame.K_s:
                    self._save()
                elif event.key == pygame.K_l:
                    self._load()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse(event.pos)

    def _handle_mouse(self, pos: tuple[int, int]) -> None:
        if self.combat.phase != "play" or self.combat.battle_over:
            return

        hand_idx = self.ui.hand_index_from_pos(len(self.combat.player.hand), pos)
        if hand_idx is not None:
            self.ui_state.selected_hand = hand_idx
            self.ui_state.selected_sacrifices.clear()
            return

        player_slot = self.ui.slot_index_from_pos(row_enemy=False, pos=pos)
        if player_slot is not None:
            if self.ui_state.selected_hand is None:
                if self.combat.board.player_slots[player_slot] is not None:
                    if player_slot in self.ui_state.selected_sacrifices:
                        self.ui_state.selected_sacrifices.remove(player_slot)
                    else:
                        self.ui_state.selected_sacrifices.add(player_slot)
                return

            ok, msg = self.combat.play_player_card(
                self.ui_state.selected_hand,
                sorted(self.ui_state.selected_sacrifices),
                player_slot,
            )
            if ok:
                if self.ui_state.selected_sacrifices:
                    self.sounds.play("sacrifice")
                self.sounds.play("place")
                self.ui_state.selected_hand = None
                self.ui_state.selected_sacrifices.clear()
            else:
                self.combat.event_log.append(msg)

    def _resolve_battle_end(self) -> None:
        if self.combat.winner == "player":
            self.victories += 1
            self._resolve_event_reward()
            self.node_index += 1
        else:
            self.losses += 1
            self.node_index = max(0, self.node_index - 1)

        if self.node_index >= len(self.map.nodes):
            self.combat.event_log.append("¡Has completado la ruta y vencido al jefe!")
            self.running = False
            return

        self._start_new_battle()

    def _resolve_event_reward(self) -> None:
        event = self.current_event
        if event == EVENT_UPGRADE and self.combat.player.deck.cards:
            card = random.choice(self.combat.player.deck.cards)
            card.attack += 1
            card.health += 1
            self.combat.event_log.append(f"Evento de mejora: {card.name} gana +1/+1.")
        elif event == EVENT_RARE:
            rare = random.choice(cards_by_rarity("rare"))
            self.combat.player.deck.add_card(rare)
            self.combat.event_log.append(f"Evento raro: obtienes {rare.name}.")
        elif event == EVENT_BOSS:
            self.combat.player.deck.add_card(card_from_name("Mantis God"))
            self.combat.event_log.append("Derrotaste al jefe: ganas Mantis God.")

    def _start_new_battle(self) -> None:
        self.ui_state = UIState()
        enemy_deck = make_enemy_deck(boss=self.current_event == EVENT_BOSS)
        enemy = Player("Leshy", enemy_deck)
        self.combat.enemy = enemy
        self.combat.board = self.combat.board.__class__()
        self.combat.player.hand.clear()
        self.combat.player.deck.shuffle()
        self.combat.enemy.hand.clear()
        self.combat.start_battle()

    def _save(self) -> None:
        state = SaveState(
            player_deck=self.combat.player.deck.to_names(),
            progress_node=self.node_index,
            victories=self.victories,
            losses=self.losses,
        )
        save_game(state)
        self.combat.event_log.append("Partida guardada.")

    def _load(self) -> None:
        state = load_game()
        if not state.player_deck:
            self.combat.event_log.append("No hay guardado válido.")
            return
        self.node_index = min(state.progress_node, len(self.map.nodes) - 1)
        self.victories = state.victories
        self.losses = state.losses
        self.combat.player.deck = Deck.from_names(state.player_deck)
        self.combat.player.deck.shuffle()
        self.combat.event_log.append("Partida cargada.")
        self._start_new_battle()
