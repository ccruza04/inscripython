"""Card model and card library utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class Card:
    """Represents a board card with combat attributes and abilities."""

    name: str
    attack: int
    health: int
    blood_cost: int
    card_type: str
    abilities: list[str] = field(default_factory=list)
    rarity: str = "common"

    def clone(self) -> "Card":
        return Card(
            name=self.name,
            attack=self.attack,
            health=self.health,
            blood_cost=self.blood_cost,
            card_type=self.card_type,
            abilities=list(self.abilities),
            rarity=self.rarity,
        )

    @property
    def is_alive(self) -> bool:
        return self.health > 0

    def take_damage(self, amount: int) -> bool:
        self.health -= amount
        return self.health <= 0

    def has_ability(self, ability: str) -> bool:
        return ability in self.abilities


CARD_LIBRARY: list[Card] = [
    Card("Stoat", 1, 3, 1, "beast"),
    Card("Wolf", 3, 2, 2, "beast"),
    Card("Bullfrog", 1, 2, 1, "beast", ["reach"]),
    Card("Sparrow", 1, 1, 1, "beast", ["flying"]),
    Card("Adder", 1, 1, 2, "beast", ["deathtouch"]),
    Card("Elk", 2, 4, 2, "beast"),
    Card("Grizzly", 4, 6, 3, "beast"),
    Card("Mantis", 1, 1, 1, "beast", ["split_strike"]),
    Card("Mantis God", 1, 1, 1, "special", ["tri_strike"], "rare"),
    Card("Raven", 2, 3, 2, "beast", ["flying"]),
    Card("Coyote", 2, 1, 1, "beast"),
    Card("Moose Buck", 3, 7, 3, "beast"),
    Card("Ant Worker", 1, 2, 1, "insect", ["swarm"]),
    Card("Alpha", 1, 2, 2, "beast", ["leader"]),
    Card("River Otter", 1, 3, 1, "beast"),
    Card("Skink", 1, 2, 1, "reptile"),
    Card("Kingfisher", 1, 1, 1, "bird", ["flying"]),
    Card("Rattler", 3, 1, 2, "reptile", ["deathtouch"]),
    Card("Urayuli", 7, 7, 4, "special", [], "rare"),
    Card("Long Elk", 1, 3, 2, "special", ["split_strike"]),
    Card("Bloodhound", 2, 3, 2, "beast"),
    Card("Hodag", 3, 4, 3, "special", [], "rare"),
]


def cards_by_rarity(rarity: str) -> list[Card]:
    return [card.clone() for card in CARD_LIBRARY if card.rarity == rarity]


def all_cards() -> list[Card]:
    return [card.clone() for card in CARD_LIBRARY]


def card_from_name(name: str) -> Card:
    for card in CARD_LIBRARY:
        if card.name == name:
            return card.clone()
    raise ValueError(f"Unknown card '{name}'")


def card_names(cards: Iterable[Card]) -> list[str]:
    return [card.name for card in cards]
