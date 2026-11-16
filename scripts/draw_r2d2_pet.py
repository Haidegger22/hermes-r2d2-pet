#!/usr/bin/env python3
"""Draw an R2-D2 pet sprite atlas by hand (pure PIL, no image model).

Atlas geometry per Hermes/petdex: 8 cols x 9 rows, cell 192x208 -> 1536x1872.
Row order (top to bottom): idle, running-right, running-left, waving, jumping,
failed, waiting, running, review.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

CELL_W, CELL_H = 192, 208
SS = 4  # supersample factor, downscaled with LANCZOS for clean edges
BASE_Y = 190.0  # foot baseline

WHITE = (240, 244, 249, 255)
WHITE_SH = (206, 215, 226, 255)
WHITE_DK = (170, 181, 194, 255)
BLUE = (43, 108, 176, 255)
BLUE_DK = (22, 52, 92, 255)
BLUE_LT = (92, 160, 226, 255)
SILVER = (152, 164, 177, 255)
DARK = (28, 34, 44, 255)
EYE_BODY = (12, 26, 40, 255)
CYAN = (110, 205, 255, 255)
RED = (228, 86, 70, 255)
AMBER = (255, 192, 84, 255)


def draw_droid(
    *,
    eye_open: float = 1.0,
    eye_color: tuple = CYAN,
    dome_turn: float = 0.0,
    leg_phase: float = 0.0,
    arm_out: float = 0.0,
    squeeze: float = 1.0,
    third_leg: bool = False,
    body_light: float = 0.0,
) -> Image.Image:
    """One upright R2-D2 frame; feet on BASE_Y, centred on x=96."""
    img = Image.new("RGBA", (CELL_W * SS, CELL_H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def Y(v: float) -> float:
        """Vertical coordinate, squashed toward the baseline."""
        return BASE_Y - (BASE_Y - v) * squeeze

    def rect(x0, y0, x1, y1, fill, r=0.0):
        box = [x0 * SS, Y(y0) * SS, x1 * SS, Y(y1) * SS]
        if r:
            d.rounded_rectangle(box, radius=max(1, r * SS * min(1, squeeze)), fill=fill)
        else:
            d.rectangle(box, fill=fill)

    def ell(x0, y0, x1, y1, fill):
        d.ellipse([x0 * SS, Y(y0) * SS, x1 * SS, Y(y1) * SS], fill=fill)

    def poly(pts, fill):
        d.polygon([(x * SS, Y(y) * SS) for x, y in pts], fill=fill)

    # ── side legs: thick, jointed, big feet ───────────────────────────────────
    swing = leg_phase * 8
    for side in (-1, 1):
        phase = swing * side
        hip_x = 96 + side * 36
        hip_y = 96
        foot_cx = 96 + side * 50 + phase
        foot_y = 178
        poly([
            (hip_x - side * 7, hip_y - 4),
            (hip_x + side * 15, hip_y + 2),
            (foot_cx + side * 20, foot_y),
            (foot_cx - side * 10, foot_y),
        ], WHITE_SH)
        poly([
            (hip_x - side * 1, hip_y + 14),
            (hip_x + side * 5, hip_y + 16),
            (foot_cx + side * 4, foot_y - 6),
            (foot_cx - side * 2, foot_y - 6),
        ], BLUE)
        # ankle joint
        ell(foot_cx - 9, foot_y - 10, foot_cx + 9, foot_y + 2, WHITE_DK)
        # foot
        rect(foot_cx - 17, foot_y, foot_cx + 17, foot_y + 12, WHITE_DK, r=5)
        rect(foot_cx - 14, foot_y + 6, foot_cx + 14, foot_y + 12, BLUE_DK, r=4)

    # ── centre leg (third leg out when standing/waving/jumping) ───────────────
    if third_leg:
        rect(84, 148, 108, 180, WHITE_SH, r=5)
        rect(88, 152, 104, 176, BLUE, r=3)
        rect(78, 178, 114, 190, WHITE_DK, r=5)
        rect(82, 184, 110, 190, BLUE_DK, r=4)
    else:
        rect(88, 152, 104, 170, WHITE_DK, r=4)

    # ── torso: taller, cylindrical ────────────────────────────────────────────
    rect(57, 84, 135, 170, WHITE, r=10)
    rect(57, 84, 68, 170, WHITE_SH, r=8)            # left shading
    rect(62, 90, 130, 100, BLUE, r=4)               # top band
    rect(62, 154, 130, 164, BLUE, r=4)              # bottom band
    rect(88, 102, 104, 152, WHITE_SH, r=3)          # centre spine
    for i in range(3):                              # vents
        rect(92, 108 + i * 10, 100, 113 + i * 10, DARK, r=1)
    rect(64, 104, 84, 136, BLUE_DK, r=4)            # side panels
    rect(108, 104, 128, 136, BLUE_DK, r=4)
    rect(66, 142, 80, 150, BLUE_LT, r=2)            # small service panel
    rect(112, 142, 126, 150, BLUE_LT, r=2)
    ell(116, 130, 126, 140, AMBER if body_light > 0.5 else RED)  # status light
    # neck ring
    rect(58, 80, 134, 87, WHITE_DK, r=3)

    # ── arm (flip-out tool arm) ───────────────────────────────────────────────
    if arm_out > 0.01:
        ax, ay = 133, 126
        ex = ax + 26 * arm_out
        rect(ax, ay - 3, ex, ay + 4, WHITE_SH, r=3)
        rect(ex - 9, ay - 9, ex + 3, ay + 10, SILVER, r=4)
        rect(ex - 6, ay - 4, ex - 1, ay + 6, BLUE_DK, r=2)

    # ── dome: sits flush on the neck ring ─────────────────────────────────────
    ell(63, 50, 129, 106, WHITE)
    ell(65, 53, 127, 102, WHITE)
    ell(69, 55, 99, 82, (252, 253, 255, 190))      # highlight
    # rotating blue panels around the dome
    cx, cy = 96, 78
    for ang, (w, h), col in (
        (-58, (13, 11), BLUE), (-26, (11, 9), BLUE_DK), (8, (10, 13), BLUE_LT),
        (44, (9, 9), BLUE), (128, (12, 10), BLUE_DK), (170, (9, 12), BLUE_LT),
    ):
        a = math.radians(ang + dome_turn * 60)
        px = cx + math.cos(a) * 22
        py = cy + math.sin(a) * 8
        rect(px - w / 2, py - h / 2, px + w / 2, py + h / 2, col, r=2)
    # two antennas, different lengths
    rect(86, 22, 88, 48, SILVER, r=1)
    rect(102, 12, 104, 48, SILVER, r=1)
    ell(101, 9, 105, 13, BLUE_LT)
    # photoreceptor: dark lens with a small cyan glint
    ell(83, 61, 109, 83, DARK)
    ell(87, 64, 105, 80, EYE_BODY)
    lens_h = max(1.2, 6 * eye_open)
    ell(96 - 6, 72 - lens_h, 96 + 6, 72 + lens_h, eye_color)
    if eye_open > 0.5:
        ell(92, 66, 97, 70, (255, 255, 255, 230))

    return img.resize((CELL_W, CELL_H), Image.LANCZOS)


def draw_droid_side(
    *,
    eye_open: float = 1.0,
    eye_color: tuple = CYAN,
    dome_turn: float = 0.0,
    leg_phase: float = 0.0,
    squeeze: float = 1.0,
    third_leg: bool = False,
    body_light: float = 0.0,
    lean: float = 0.0,
    rolling: bool = False,
    wheel: float = 0.0,
    dust: float = 0.0,
) -> Image.Image:
    """R2-D2 в профиль (starboard elevation), лицом вправо.

    Слои: шасси (дальняя нога + третья нога с гусеницей) → корпус с куполом →
    ближняя нога сверху корпуса (в профиль она к нам ближе всего).
    """
    def prims(draw):
        def Y(v: float) -> float:
            return BASE_Y - (BASE_Y - v) * squeeze

        def rect(x0, y0, x1, y1, fill, r=0.0):
            box = [x0 * SS, Y(y0) * SS, x1 * SS, Y(y1) * SS]
            if r:
                draw.rounded_rectangle(box, radius=max(1, r * SS * min(1, squeeze)), fill=fill)
            else:
                draw.rectangle(box, fill=fill)

        def ell(x0, y0, x1, y1, fill):
            draw.ellipse([x0 * SS, Y(y0) * SS, x1 * SS, Y(y1) * SS], fill=fill)

        def poly(pts, fill):
            draw.polygon([(x * SS, Y(y) * SS) for x, y in pts], fill=fill)

        return rect, ell, poly, draw, Y

    def foot(rect, ell, poly, *, cx, tone, dome_tone, heel, phase):
        """Ступня в профиль: трапеция, куполообразный кожух, колесо у пятки."""
        poly([(cx - 11, 168), (cx + 11, 168), (cx + 17, 189), (cx - 17, 189)], tone)
        ell(cx - 14, 162, cx + 14, 174, dome_tone)
        rect(cx - 16, 186, cx + 16, 190, (214, 221, 230, 255), r=1)
        poly([(cx + 4, 172), (cx + 16, 172), (cx + 17, 189), (cx + 6, 189)], (30, 62, 104, 255))
        ell(heel - 5.0, 180, heel + 5.0, 190, (48, 54, 62, 255))
        ell(heel - 3.6, 181.4, heel + 3.6, 188.6, (152, 162, 174, 255))
        for k in range(2):
            a = phase * 2 * math.pi + k * math.pi
            ell(heel + math.cos(a) * 1.9 - 1.0, 185 + math.sin(a) * 1.9 - 1.0,
                heel + math.cos(a) * 1.9 + 1.0, 185 + math.sin(a) * 1.9 + 1.0, (36, 41, 48, 255))

    # ── шасси ────────────────────────────────────────────────────────────────
    chassis = Image.new("RGBA", (CELL_W * SS, CELL_H * SS), (0, 0, 0, 0))
    rect, ell, poly, draw, Y = prims(ImageDraw.Draw(chassis))

    # дальняя нога
    poly([(60, 116), (74, 116), (70, 164), (56, 164)], (190, 200, 211, 255))
    rect(56, 160, 74, 176, (190, 200, 211, 255), r=3)
    foot(rect, ell, poly, cx=58, tone=(178, 188, 200, 255),
         dome_tone=(200, 209, 220, 255), heel=48, phase=wheel)

    # третья нога + гусеничный привод (уже, темнее, с зазором от ступней)
    rect(86, 162, 94, 176, WHITE_SH, r=2)
    rect(74, 172, 96, 190, (96, 106, 118, 255), r=4)                    # кожух
    rect(76, 175, 94, 187, (46, 52, 60, 255), r=3)                      # лента
    for k in range(4):
        tx = 77 + ((k * 4.2 + wheel * 8) % 15)
        rect(tx, 174, tx + 1.6, 176.4, (198, 205, 214, 255))
        rect(tx, 185.6, tx + 1.6, 188, (198, 205, 214, 255))
    ell(84, 178, 92, 186, (168, 178, 191, 255))                         # ролик

    # ── корпус + купол ───────────────────────────────────────────────────────
    torso = Image.new("RGBA", (CELL_W * SS, CELL_H * SS), (0, 0, 0, 0))
    rect, ell, poly, draw, Y = prims(ImageDraw.Draw(torso))

    rect(64, 92, 124, 170, WHITE, r=5)                                  # цилиндр: стенки прямые
    rect(64, 92, 74, 170, WHITE_SH, r=4)                                # тень сзади
    rect(64, 129, 124, 132, WHITE_SH)                                   # средний шов
    rect(64, 164, 124, 170, WHITE_SH, r=3)                              # юбка
    rect(104, 100, 120, 126, BLUE, r=3)                                 # передняя дверца
    rect(80, 104, 98, 128, BLUE_DK, r=3)                                # арочная панель
    rect(87, 110, 92, 124, DARK, r=1)
    rect(84, 138, 96, 146, WHITE_SH, r=2)                               # hard data input
    ell(87, 140, 90, 144, DARK)
    ell(92, 140, 95, 144, DARK)
    for k in range(3):                                                  # жалюзи сзади
        rect(68, 150 + k * 5, 82, 152.4 + k * 5, DARK, r=0.8)
    poly([(110, 138), (117, 138), (121, 146), (117, 154), (110, 154), (106, 146)],
         (208, 216, 226, 255))                                          # восьмигранный порт
    ell(112, 157, 120, 165, AMBER if body_light > 0.5 else RED)         # индикатор

    rect(62, 84, 126, 94, WHITE_DK, r=3)                                # основание купола
    ell(64, 58, 124, 116, WHITE)                                        # полусфера
    ell(66, 60, 122, 114, WHITE)
    ell(70, 62, 96, 84, (252, 253, 255, 190))
    for ang, (w, h), col in ((-70, (16, 8), BLUE), (-108, (12, 8), BLUE_DK),
                             (-38, (12, 7), BLUE_LT), (-92, (9, 6), BLUE)):
        a = math.radians(ang + dome_turn * 40)
        px = 98 + math.cos(a) * 26
        py = 88 + math.sin(a) * 8
        rect(px - w / 2, py - h / 2, px + w / 2, py + h / 2, col, r=1.5)
    rect(90, 36, 92, 62, SILVER, r=1)                                   # антенны
    rect(99, 28, 101, 60, SILVER, r=1)
    ell(98, 25, 102, 29, (96, 156, 224, 255))
    rect(107, 72, 115, 86, DARK, r=3)                                   # радарный глаз
    ell(111, 70, 121, 86, DARK)
    lens_h = max(1.2, 3.8 * eye_open)
    ell(114, 78 - lens_h, 121, 78 + lens_h, EYE_BODY)
    ell(116, 78 - lens_h / 2, 120, 78 + lens_h / 2, eye_color)
    if eye_open > 0.5:
        ell(117, 73, 120, 76, (255, 255, 255, 230))

    # ── ближняя нога: отдельный слой ПОВЕРХ корпуса, стоит на земле ───────────
    near = Image.new("RGBA", (CELL_W * SS, CELL_H * SS), (0, 0, 0, 0))
    rect, ell, poly, draw, Y = prims(ImageDraw.Draw(near))
    ell(96, 98, 122, 124, SILVER)                                       # плечевой диск
    ell(99, 101, 119, 121, WHITE)
    ell(105, 107, 113, 115, (96, 156, 224, 255))
    poly([(98, 118), (122, 118), (120, 162), (100, 162)], WHITE)        # балка
    poly([(103, 124), (117, 124), (115, 158), (105, 158)], BLUE)        # синяя полоса
    rect(98, 158, 122, 174, WHITE_DK, r=4)                              # лодыжка
    foot(rect, ell, poly, cx=120, tone=WHITE_DK, dome_tone=WHITE, heel=134, phase=wheel + 0.3)

    if lean:
        torso = torso.rotate(-lean, resample=Image.BICUBIC, center=(96 * SS, (BASE_Y - 84) * SS))
    img = Image.alpha_composite(chassis, torso)
    img = Image.alpha_composite(img, near)

    if dust > 0.03:
        puff = Image.new("RGBA", (CELL_W * SS, CELL_H * SS), (0, 0, 0, 0))
        pd = ImageDraw.Draw(puff)
        for idx, (px, py, pr) in enumerate(((36, 186, 8), (26, 191, 6), (18, 187, 4))):
            grow = min(1.0, dust * 1.15) * (1 - idx * 0.22)
            if grow <= 0.05:
                continue
            alpha = int(105 * (1 - idx * 0.2) * min(1.0, dust) * 1.35)
            pd.ellipse([(px - pr * grow) * SS, (py - pr * 0.6 * grow) * SS,
                        (px + pr * grow) * SS, (py + pr * 0.6 * grow) * SS],
                       fill=(208, 216, 226, min(120, alpha)))
        img.alpha_composite(puff.filter(ImageFilter.GaussianBlur(3)))

    return img.resize((CELL_W, CELL_H), Image.LANCZOS)


def frame(kind: str, i: int) -> tuple[Image.Image, float]:
    """Frame *i* (0..5) of a state, plus its vertical bob in px."""
    t = i / 6.0
    tau = 2 * math.pi * t

    if kind == "idle":
        return draw_droid(eye_open=0.25 if i == 4 else 1.0,
                          dome_turn=0.05 * math.sin(tau),
                          body_light=1 if i in (1, 4) else 0), -2 * (0.5 - 0.5 * math.cos(tau * 2))

    if kind in ("running-right", "running"):
        wheel = i / 6.0
        puff = (0.30, 0.65, 0.95, 0.75, 0.45, 0.20)[i]
        return draw_droid_side(rolling=True, wheel=wheel, dust=puff,
                               dome_turn=0.06 * math.sin(2 * math.pi * wheel),
                               eye_open=1.0,
                               lean=(-10 if kind == "running-right" else -8) - 1.0 * math.sin(2 * math.pi * wheel),
                               body_light=1 if kind == "running" else 0), 0.0

    if kind == "waving":
        out = math.sin(tau) if math.sin(tau) > 0 else 0.0
        return draw_droid(arm_out=min(1.0, out * 1.7), third_leg=True,
                          dome_turn=0.25 * math.sin(tau * 2)), -1.5 * math.sin(tau)

    if kind == "jumping":
        plan = [0.90, 1.06, 1.0, 1.0, 0.94, 0.98]
        heights = [2, -10, -22, -16, 0, 1]
        airborne = i in (2, 3)
        return draw_droid_side(squeeze=plan[i], third_leg=airborne,
                               dome_turn=0.12 if airborne else 0.0,
                               body_light=1 if airborne else 0), heights[i]

    if kind == "failed":
        return draw_droid(eye_open=1.0, eye_color=RED, dome_turn=-0.5,
                          squeeze=0.95), 2 + (1 if i % 2 else 0)

    if kind == "waiting":
        return draw_droid(eye_open=0.7, dome_turn=0.1 * math.sin(tau),
                          body_light=1 if i in (2, 3) else 0,
                          third_leg=True), -1.5 * (0.5 - 0.5 * math.cos(tau))

    if kind == "review":
        return draw_droid(eye_open=1.0, dome_turn=math.sin(tau) * 1.2,
                          body_light=1 if i in (0, 3) else 0), -1 * (0.5 - 0.5 * math.cos(tau * 2))

    raise SystemExit(f"unknown kind {kind}")


ROWS = [
    ("idle", 6), ("running-right", 6), ("running-left", 6), ("waving", 6),
    ("jumping", 6), ("failed", 6), ("waiting", 6), ("running", 6), ("review", 6),
]


def build_atlas() -> Image.Image:
    atlas = Image.new("RGBA", (8 * CELL_W, 9 * CELL_H), (0, 0, 0, 0))
    for row, (kind, count) in enumerate(ROWS):
        for col in range(count):
            if kind == "running-left":
                src, bob = frame("running-right", col)
                cell = src.transpose(Image.FLIP_LEFT_RIGHT)
            else:
                cell, bob = frame(kind, col)
            layer = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
            shadow = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
            ImageDraw.Draw(shadow).ellipse([20, 184, 136, 197], fill=(0, 0, 0, 105))
            layer.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(3)))
            layer.alpha_composite(cell, (0, int(round(bob))))
            atlas.alpha_composite(layer, (col * CELL_W, row * CELL_H))
    return atlas


def self_check(atlas: Image.Image) -> None:
    """Контракт petdex: 1536×1872, и колонки 7–8 каждой строки должны быть пустыми."""
    assert atlas.size == (8 * CELL_W, 9 * CELL_H), f"размер атласа: {atlas.size}"
    for row in range(9):
        for col in (6, 7):
            box = (col * CELL_W, row * CELL_H, (col + 1) * CELL_W, (row + 1) * CELL_H)
            assert atlas.crop(box).getbbox() is None, f"лишние пиксели в колонке {col}, строке {row}"


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Нарисовать атлас R2-D2 для Hermes (petdex, 1536x1872).")
    ap.add_argument("-o", "--out", default="r2_atlas.png", help="куда сохранить PNG")
    ap.add_argument("--ss", type=int, default=SS, help="суперсэмплинг (по умолчанию 4)")
    ap.add_argument("--no-check", action="store_true", help="не проверять контракт после сборки")
    args = ap.parse_args()

    if args.ss != SS:  # меняется только через модуль: SS участвует в замыканиях примитивов
        globals()["SS"] = args.ss

    atlas = build_atlas()
    if not args.no_check:
        self_check(atlas)
    out = Path(args.out)
    atlas.save(out)
    print(f"{out} — {atlas.size[0]}x{atlas.size[1]}, Pillow {Image.__version__ if hasattr(Image, '__version__') else 'n/a'}")

