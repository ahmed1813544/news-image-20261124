#!/usr/bin/env python3
"""THE WORLD TODAY - Tuesday 24 November 2026 in one image.

Stdlib-only program. Draws a newspaper front page summing up the
world news of Tuesday 24 November 2026 (verified from that day's
reporting) and writes it to /output/entry.png as a palette PNG.
Runs with no network, no clock and no randomness: two runs write
identical bytes.
"""

import os
import struct
import zlib
from binascii import crc32

# ---------------------------------------------------------------- font
# Hand-drawn 5x7 bitmap font, uppercase + digits + punctuation.
# Each glyph is 7 rows of 5 characters: '#' is ink, '.' is blank.
FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '-': (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    '%': ("##...", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    '$': ("..#..", ".####", "#.#.#", ".###.", "..#.#", "####.", "..#.."),
    '/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    '(': ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ')': ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '*': (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    '&': (".##..", "#..#.", "#.#..", ".#.#.", "#..#.", "#.#..", ".##.#"),
    '|': ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
}

# ---------------------------------------------------------------- canvas
W, H = 1024, 1024


class Canvas:
    """Flat RGB canvas on a bytearray; palette PNG out."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bytes(bg) * (w * h))

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c, thick=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            self.rect(x - thick // 2, y - thick // 2, thick, thick, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, c, fill=False):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.px(xx, yy, c)
                else:
                    if r * r - 2 * r <= d2 <= r * r:
                        self.px(xx, yy, c)

    def text(self, x, y, s, scale, c):
        """Draw uppercase text; unknown chars become spaces."""
        cx = x
        for ch in s.upper():
            g = FONT.get(ch, FONT[' '])
            for ry, row in enumerate(g):
                for rx, bit in enumerate(row):
                    if bit == '#':
                        self.rect(cx + rx * scale, y + ry * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale):
        return len(s) * 6 * scale

    def center(self, y, s, scale, c):
        self.text((self.w - self.text_w(s, scale)) // 2, y, s, scale, c)


def wrap(s, width_chars):
    """Greedy word wrap to at most width_chars per line."""
    lines, cur = [], ""
    for word in s.upper().split(" "):
        if cur and len(cur) + 1 + len(word) > width_chars:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + " " + word) if cur else word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- png
def png_bytes(cv):
    """Encode the canvas as a palette PNG (colour type 3)."""
    palette, index = [], {}
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        for x in range(cv.w):
            i = (y * cv.w + x) * 3
            key = bytes(cv.buf[i:i + 3])
            k = index.get(key)
            if k is None:
                k = len(palette)
                index[key] = k
                palette.append(key)
            raw.append(k)
    if len(palette) > 256:
        raise ValueError("too many colours: %d" % len(palette))
    plte = b"".join(palette)
    data = zlib.compress(bytes(raw), 9)

    def chunk(kind, payload):
        return (struct.pack(">I", len(payload)) + kind + payload +
                struct.pack(">I", crc32(kind + payload) & 0xffffffff))

    out = bytearray(b"\x89PNG\r\n\x1a\n")
    out += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 3, 0, 0, 0))
    out += chunk(b"PLTE", plte)
    out += chunk(b"IDAT", data)
    out += chunk(b"IEND", b"")
    return bytes(out)


# ---------------------------------------------------------------- colours
PAPER = (247, 243, 232)
INK = (18, 22, 30)
NAVY = (20, 33, 61)
NAVY_LT = (38, 58, 94)
RED = (178, 34, 34)
GREEN = (27, 120, 55)
GREEN_DK = (16, 84, 36)
GOLD = (184, 134, 11)
GOLD_LT = (242, 220, 150)
GREY = (105, 105, 105)
RULE = (150, 145, 130)
CHIP_BG = (226, 240, 224)
AMBER = (176, 92, 8)
TEAL = (11, 110, 110)
PURPLE = (96, 48, 140)
BLUE = (24, 90, 160)
ORANGE = (196, 84, 16)

REGION_COLOUR = {
    "USA": NAVY, "EUROPE": BLUE, "ASIA": TEAL, "INDIA": (150, 60, 20),
    "MIDDLE EAST": AMBER, "AFRICA": ORANGE, "SPORT": GREEN,
    "TECH": PURPLE, "MARKETS": GOLD, "GLOBAL": GREY, "UK": (90, 40, 90),
    "PAKISTAN": (20, 110, 60),
}

# ---------------------------------------------------------------- stories
# (region, headline, summary) - every item first reported on 24 Nov 2026
# in the day's editions, or dated 24 Nov in the source that carried it.
STORIES = [
    ("USA", "GOMEZ QUITS CONGRESS",
     "Rep. Jimmy Gomez resigns, effective Dec 1, after the Ethics panel "
     "found evidence of sexual misconduct."),
    ("TECH", "STATES SUE MUSK OVER GROK",
     "US states sue Musk companies over a flood of sexualised images "
     "made with the AI chatbot Grok."),
    ("USA", "DEMOCRATS TAKE THE HOUSE",
     "Democrats clinch their biggest House majority in decades, with "
     "power to block Trump's agenda."),
    ("USA", "TRUMP'S HEALTHCARE OFFER",
     "Trump signals a possible healthcare deal with the Democrats."),
    ("USA", "PHILIPPINES GETS $2.4BN",
     "Trump offers the Philippines $2.4bn for self-defence - with a catch "
     "attached to the arms package."),
    ("TECH", "MEGASPEED BLACKLISTED",
     "Commerce blacklists Megaspeed hours after Huang's return, the firm "
     "at the heart of the chip probe."),
    ("USA", "VANCE IS TRUMP'S EMISSARY",
     "Vance is tapped as Trump's emissary to the Nvidia board amid the "
     "fight over the CEO's reinstatement."),
    ("PAKISTAN", "PETROL PRICE CUT",
     "Petrol falls Rs3 a litre to Rs319; diesel unchanged at Rs357."),
    ("PAKISTAN", "LAHORE CHOKES",
     "Lahore remains the world's most polluted city as its air quality "
     "index crosses 500."),
    ("ASIA", "MUNIR MEETS ANWAR",
     "Pakistan and Malaysia discuss military cooperation as Field Marshal "
     "Asim Munir meets Anwar Ibrahim."),
    ("INDIA", "MODI OPENS AI CENTRE",
     "Modi inaugurates an AI centre at IIT Patna and launches a Rs400 "
     "crore research park project."),
    ("INDIA", "A TRAIN TO NEPAL",
     "Modi and Nepal PM Balendra Shah flag off the Saryu-Kamala Express "
     "to Janakpur Dham."),
    ("INDIA", "BORDER TALKS HELD",
     "Indian and Chinese commanders hold military talks in Arunachal "
     "Pradesh to reduce border tensions."),
    ("ASIA", "S&P CUTS MANILA FORECAST",
     "S&P cuts the Philippines' growth outlook to 2.4% as weak government "
     "spending weighs on demand."),
    ("ASIA", "BUDGET ROW IN MANILA",
     "Senator Lacson flags projects funded twice, even three times, in "
     "the proposed 2027 national budget."),
    ("ASIA", "DUTERTE TRIAL ON TRACK",
     "The impeachment trial of VP Sara Duterte is on track to end before "
     "the Senate's Christmas break."),
    ("ASIA", "THAI COURT UPHOLDS VERDICT",
     "A Thai court upholds the verdict against an opposition lawmaker in "
     "a closely watched case."),
    ("ASIA", "NEPAL PM IN INDIA",
     "Nepal PM Balendra Shah is in India for economic and energy talks "
     "with Prime Minister Modi."),
    ("EUROPE", "KYIV STRIKES KILL 14",
     "Russian drone and missile strikes kill at least 14 in Ukraine's "
     "Kyiv region, hitting homes in Dymer."),
    ("EUROPE", "UKRAINE SINKS WARSHIP",
     "Zelensky says seven sea drones sank the Russian corvette Merkury "
     "at Libya's Benghazi port."),
    ("EUROPE", "EU SANCTIONS PLAN",
     "The EU Commission proposes new Russia sanctions, including a ban on "
     "Russian athletes and ex-fighters."),
    ("EUROPE", "REFINERY HALTED",
     "Russia's Novoshakhtinsk refinery halts after a massive Ukrainian "
     "missile and drone attack."),
    ("AFRICA", "DRONES HIT KHARTOUM",
     "Drone attacks hit homes and a UN building in Sudan's capital as "
     "the war grinds on."),
    ("MIDDLE EAST", "GAZA'S TOXIC LEGACY",
     "Oxfam warns Israel's bombardment has left Gaza's air, soil and "
     "water toxic for decades."),
    ("MIDDLE EAST", "HOUTHI STRIKE CLAIM",
     "Yemen's Houthis claim an attack on Saudi Arabia's Rabigh oil "
     "refinery; Saudi strikes hit Yemen."),
    ("EUROPE", "TURKEY MEDIA PROTEST",
     "Thousands protest the closure of media outlets in Turkey, in one "
     "of the year's biggest press rallies."),
    ("EUROPE", "MACRON EYES REFORM",
     "Macron eyes constitutional changes to curb public spending as "
     "France faces calls for restraint."),
    ("GLOBAL", "UN CHIEF'S AI WARNING",
     "The UN chief calls for an AI risk management framework within a "
     "year, warning of runaway systems."),
    ("UK", "CONCERT EVACUATED",
     "Thousands are evacuated from a UK concert after an 'unknown "
     "substance' is released inside."),
    ("SPORT", "ALCARAZ WINS ATP FINALS",
     "Carlos Alcaraz beats Alexander Zverev in Turin to win his first "
     "ATP Finals title."),
    ("SPORT", "TEST ENDS IN A DRAW",
     "India and New Zealand draw the first Test in Wellington after a "
     "strong fightback; Pant hits 128."),
    ("SPORT", "CHESS TITLE BEGINS",
     "Gukesh begins his world title defence against Sindarov in Geneva "
     "in the World Chess Championship."),
    ("SPORT", "FERRARI UNVEILS 296",
     "Ferrari unveils the 296 Challenge Stradale and 296 Challenge Evo "
     "at its Finali Mondiali in Spain."),
    ("MARKETS", "TESLA SURGES 12%",
     "Tesla jumps as Musk promises a wide rollout of Full Self-Driving "
     "v15 next month."),
    ("ASIA", "US DRONE CRASHES",
     "A US MQ-9 drone deployed in South Korea crashes off the coast of "
     "Gunsan, officials report."),
    ("UK", "WILLIAM'S ROYAL PLAN",
     "Prince William plans to strip Harry and Meghan of royal titles "
     "when he becomes king: report."),
]

MARKETS = ("MARKETS  |  S&P 500 +4.7%  |  NASDAQ +6.5%  |  NIKKEI -5.1%  |  "
           "FTSE +1.3%  |  BRENT $86.78 -3.5%  |  GOLD +4.2%  |  "
           "SILVER $42.60 +4.0%  |  BITCOIN $55,150")

FOOTER = ("37 STORIES FROM TUESDAY 24 NOVEMBER 2026 - VERIFIED FROM THE DAY'S "
          "REPORTS - SOURCES: REUTERS, WSJ, AP, AFP, SCMP, AL JAZEERA, CNN")


# ---------------------------------------------------------------- layout
def draw_masthead(cv):
    cv.rect(0, 0, W, 86, NAVY)
    # small globe at the left
    cv.circle(52, 43, 24, GOLD_LT, fill=False)
    cv.line(28, 43, 76, 43, GOLD_LT)
    cv.line(52, 19, 52, 67, GOLD_LT)
    for r in (12, 18):
        cv.circle(52, 43, r, GOLD_LT)
    cv.text(92, 14, "THE WORLD TODAY", 6, (255, 255, 255))
    cv.text(92, 58, "TUESDAY, 24 NOVEMBER 2026  -  THE DAY IN ONE PAGE",
            2, GOLD_LT)
    cv.rect(0, 86, W, 5, RED)


def draw_hero(cv, y):
    """Lead story: Nvidia brings Jensen Huang back."""
    h = 178
    cv.rect(16, y, W - 32, h, CHIP_BG)
    cv.rect(16, y, W - 32, h, NAVY_LT)  # border via inner panel below
    cv.rect(18, y + 2, W - 36, h - 4, CHIP_BG)
    tx = 36
    cv.text(tx, y + 16, "THE COMEBACK  -  BUSINESS", 2, RED)
    cv.text(tx, y + 44, "HUANG IS BACK", 5, NAVY)
    cv.text(tx, y + 92,
            "NVIDIA REINSTATES ITS CEO 11 DAYS AFTER HE QUIT -", 2, INK)
    cv.text(tx, y + 114,
            "TRUMP: 'I MADE THE DEAL' - SHARES SOAR 31%", 2, INK)
    cv.text(tx, y + 142,
            "BOARD VOTES UNANIMOUSLY AFTER US GOVERNMENT INPUT -", 1, GREY)
    cv.text(tx, y + 154,
            "NASDAQ +6.5%, S&P 500 +4.7% AS THE AI TRADE ROARS BACK", 1, GREY)
    # right-hand illustration: a green chip, a rising chart, +31% badge
    ix, iy = 700, y + 18
    cv.rect(ix, iy, 150, 110, GREEN_DK)
    cv.rect(ix + 6, iy + 6, 138, 98, GREEN)
    for px in (ix + 16, ix + 46, ix + 76, ix + 106):
        cv.rect(px, iy - 8, 8, 8, GREEN_DK)
        cv.rect(px, iy + 110, 8, 8, GREEN_DK)
    cv.text(ix + 34, iy + 14, "NVDA", 3, (255, 255, 255))
    cv.text(ix + 22, iy + 44, "AI CHIP", 2, (220, 255, 220))
    # rising arrow across the lower half of the chip, below the text
    cv.line(ix + 14, iy + 98, ix + 58, iy + 80, (255, 255, 255), 3)
    cv.line(ix + 58, iy + 80, ix + 104, iy + 64, (255, 255, 255), 3)
    cv.line(ix + 104, iy + 64, ix + 92, iy + 66, (255, 255, 255), 3)
    cv.line(ix + 104, iy + 64, ix + 100, iy + 76, (255, 255, 255), 3)
    # rising bars under the chip
    bx, by = ix + 4, iy + 120
    for i, bh in enumerate((10, 18, 26)):
        cv.rect(bx + i * 52, by + 28 - bh, 40, bh, (27, 120, 55))


def draw_markets(cv, y):
    cv.rect(0, y, W, 26, GOLD)
    cv.text(12, y + 9, MARKETS, 1, (255, 255, 255))


def draw_story(cv, x, y, w, region, headline, summary):
    colour = REGION_COLOUR.get(region, GREY)
    cv.rect(x, y + 2, 10, 10, colour)
    cv.text(x + 16, y, region, 1, colour)
    hl = wrap(headline, (w - 4) // 12)
    hy = y + 13
    for ln in hl[:2]:
        cv.text(x, hy, ln, 2, INK)
        hy += 15
    sm = wrap(summary, (w - 4) // 6)
    sy = hy + 1
    for ln in sm[:2]:
        cv.text(x, sy, ln, 1, (58, 58, 58))
        sy += 9
    return sy + 6


def draw_grid(cv, y):
    cols = 3
    col_w = 316
    gap = 14
    x0 = 16
    per_col = (len(STORIES) + cols - 1) // cols
    bottom = y
    for c in range(cols):
        cx = x0 + c * (col_w + gap)
        cy = y
        for st in STORIES[c * per_col:(c + 1) * per_col]:
            cy = draw_story(cv, cx, cy, col_w, *st)
        bottom = max(bottom, cy)
        if c < cols - 1:
            cv.vline(cx + col_w + gap // 2, y, bottom - y, RULE)
    return bottom


def draw_footer(cv, y):
    cv.rect(0, y, W, 3, RED)
    cv.text(16, y + 10, FOOTER, 1, GREY)


# ---------------------------------------------------------------- build
def build():
    cv = Canvas(W, H, PAPER)
    draw_masthead(cv)
    draw_hero(cv, 99)
    draw_markets(cv, 285)
    grid_end = draw_grid(cv, 320)
    draw_footer(cv, 972)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    path = os.path.join(out_dir, "entry.png")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(build())
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
