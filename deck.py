"""Deck and draw pile utilities."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from card import Card, all_cards, card_from_name


@dataclass
class Deck:
    cards: list[Card] = field(default_factory=list)

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def draw(self) -> Card | None:
        if not self.cards:
            return None
        return self.cards.pop(0)

    def add_card(self, card: Card) -> None:
        self.cards.append(card)

    def to_names(self) -> list[str]:
        return [card.name for card in self.cards]

    @classmethod
    def from_names(cls, names: list[str]) -> "Deck":
        return cls([card_from_name(name) for name in names])


def make_starter_deck() -> Deck:
    base = [
        "Stoat",
        "Stoat",
        "Bullfrog",
        "Sparrow",
        "Coyote",
        "Wolf",
        "Wolf",
        "River Otter",
        "Skink",
        "Kingfisher",
        "Adder",
        "Mantis",
    ]
    deck = Deck([card_from_name(name) for name in base])
    deck.shuffle()
    return deck


def make_enemy_deck(boss: bool = False) -> Deck:
    pool = all_cards()
    weight = 14 if boss else 10
    cards = random.sample(pool, k=weight)
    if boss:
        cards.append(card_from_name("Grizzly"))
        cards.append(card_from_name("Urayuli"))
    deck = Deck(cards)
    deck.shuffle()
    return deck
