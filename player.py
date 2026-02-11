"""Player model and gameplay actions."""

from __future__ import annotations

from dataclasses import dataclass, field

from card import Card
from deck import Deck


@dataclass
class Player:
    name: str
    deck: Deck
    hand: list[Card] = field(default_factory=list)

    def draw_card(self) -> Card | None:
        card = self.deck.draw()
        if card is not None:
            self.hand.append(card)
        return card

    def remove_from_hand(self, index: int) -> Card:
        return self.hand.pop(index)

    def add_to_hand(self, card: Card) -> None:
        self.hand.append(card)

    def has_playable(self, sacrifices_available: int) -> bool:
        return any(card.blood_cost <= sacrifices_available for card in self.hand)
