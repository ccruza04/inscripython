"""Entrypoint for Inscripython."""

from __future__ import annotations

from game import InscripythonGame


def main() -> None:
    game = InscripythonGame()
    game.run()


if __name__ == "__main__":
    main()
