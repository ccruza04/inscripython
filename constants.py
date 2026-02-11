"""Global constants for the Inscripython game."""

from __future__ import annotations

from pathlib import Path

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

BOARD_SLOTS = 4
STARTING_HAND_SIZE = 3
MAX_BALANCE = 10
WIN_BALANCE = 5

CARD_WIDTH = 150
CARD_HEIGHT = 210

PLAYER_ROW_Y = 450
ENEMY_ROW_Y = 180
SLOT_GAP = 180
FIRST_SLOT_X = 260

HAND_Y = 640
HAND_SPACING = 130

BG_COLOR = (22, 18, 15)
PANEL_COLOR = (47, 39, 33)
TEXT_COLOR = (235, 225, 210)
ACCENT_COLOR = (168, 125, 84)
GOOD_COLOR = (110, 190, 90)
BAD_COLOR = (200, 80, 80)

SAVE_FILE = Path("savegame.json")
ASSETS_DIR = Path("assets")

EVENT_COMBAT = "combat"
EVENT_UPGRADE = "upgrade"
EVENT_RARE = "rare"
EVENT_BOSS = "boss"

PHASE_DRAW = "draw"
PHASE_PLAY = "play"
PHASE_ATTACK = "attack"
PHASE_ENEMY = "enemy"

SOUND_SAMPLE_RATE = 44100
