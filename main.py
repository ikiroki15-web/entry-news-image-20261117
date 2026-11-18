# WORLD NEWS — Tuesday, 17 November 2026
# A one-day newspaper front page, drawn from scratch at runtime.
# Python 3.13, standard library only, no network, fully deterministic:
# the same bytes come out of every run. Writes /output/entry.png
# (or $MAKEFUN_OUTPUT_DIR/entry.png), a 1024x1024 PNG.
#
# News verified on 17-18 Nov 2026 from BBC, Reuters/Kyodo, AP/AFP and
# China's Foreign Ministry:
#   1. Ukraine strike partly collapses the Kerch (Crimean) Bridge.
#   2. Russian missiles damage two bridges in Kyiv.
#   3. Suspected Russian planes enter Japanese airspace; jets scramble.
#   4. Mongolia's President Khurelsukh resigns over graft claims.
#   5. US loses measles elimination status after 26 years.
#   6. Russian military plane crashes in Kemerovo; 19 killed.
#   7. APEC opens in Shenzhen; Trump, Xi, Putin set for first 3-way talks.
#   8. Israeli settlers shoot dead a 72-year-old Palestinian woman
#      near Jericho, the Palestinian Health Ministry says.
# Dropped as not a 17 Nov event: the Gaza aid joint statement (issued
# 15-16 Nov), Depardieu dropping his appeal (announced Mon 16 Nov),
# an Epstein-death claim from one forensic expert (unverified), and a
# reported US strike on Qeshm Island (single aggregator source only).

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 231)   # newsprint cream
INK = (17, 17, 17)        # near-black
RED = (178, 34, 34)       # headline red
WHITE = (255, 255, 255)
GREY = (90, 90, 90)
LIGHT = (232, 226, 212)   # panel tint
BLUE = (28, 68, 140)
TEAL = (14, 110, 110)
GREEN = (34, 110, 60)
PURPLE = (104, 52, 130)
BROWN = (122, 74, 30)
ORANGE = (210, 110, 20)
GOLD = (212, 160, 30)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 pixels, "#" = on, "." = off.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", "..#..", ".#..."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
}


def text_width(text, scale):
    """Pixel width of text at the given scale (6 px advance per glyph)."""
    return len(text) * 6 * scale - scale


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines fitting max_width."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.rect(x0 - thick // 2, y0 - thick // 2, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=False):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy)
                if fill:
                    if d <= r * r:
                        self.set(xx, yy, color)
                else:
                    if r * r - 2 * r <= d <= r * r:
                        self.set(xx, yy, color)

    def fill_poly(self, pts, color):
        """Scanline fill of a polygon given as [(x, y), ...]."""
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                for x in range(int(xs[j]), int(xs[j + 1]) + 1):
                    self.set(x, y, color)

    def glyph(self, x, y, ch, scale, color):
        rows = FONT.get(ch.upper(), FONT["?"])
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                if bit == "#" or bit == "1":
                    self.rect(x + c * scale, y + r * scale, scale, scale, color)

    def text(self, x, y, s, scale, color):
        for ch in s:
            self.glyph(x, y, ch, scale, color)
            x += 6 * scale
        return x

    def text_center(self, cx, y, s, scale, color):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color)

    def para(self, x, y, s, scale, color, max_width, line_gap=3):
        lines = wrap_text(s, max_width, scale)
        for ln in lines:
            self.text(x, y, ln, scale, color)
            y += 7 * scale + line_gap
        return y


# -------------------------------------------------------------- pictograms
def burst(cv, cx, cy, r, color):
    """Starburst: 8 spokes from the centre."""
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                   (1, 1), (-1, -1), (1, -1), (-1, 1)):
        cv.line(cx, cy, cx + dx * r, cy + dy * r, color, 3)
    cv.circle(cx, cy, r // 3, color, fill=True)


def pic_bridge(cv, x, y):
    """Kerch bridge: deck with a broken middle span, explosion above."""
    cv.rect(x + 6, y + 78, 108, 6, INK)          # deck
    cv.rect(x + 6, y + 84, 6, 22, INK)           # left pier
    cv.rect(x + 108, y + 84, 6, 22, INK)         # right pier
    cv.line(x + 12, y + 78, x + 38, y + 52, INK, 3)   # left arch
    cv.line(x + 38, y + 52, x + 52, y + 78, INK, 3)
    cv.line(x + 68, y + 78, x + 82, y + 52, INK, 3)   # right arch
    cv.line(x + 82, y + 52, x + 108, y + 78, INK, 3)
    cv.line(x + 52, y + 78, x + 60, y + 92, INK, 3)   # fallen span
    cv.line(x + 60, y + 92, x + 68, y + 78, INK, 3)
    burst(cv, x + 60, y + 30, 20, ORANGE)
    cv.hline(x + 6, y + 112, 108, BLUE, 2)       # water
    cv.hline(x + 20, y + 118, 80, BLUE, 2)


def pic_kyiv(cv, x, y):
    """Two Kyiv bridges under missile streaks, skyline behind."""
    cv.rect(x + 10, y + 60, 18, 46, GREY)        # towers
    cv.rect(x + 34, y + 48, 16, 58, GREY)
    cv.rect(x + 88, y + 66, 18, 40, GREY)
    cv.rect(x + 6, y + 96, 108, 5, INK)          # bridge deck
    cv.rect(x + 14, y + 101, 5, 12, INK)
    cv.rect(x + 100, y + 101, 5, 12, INK)
    cv.line(x + 20, y + 20, x + 62, y + 88, RED, 3)    # missile streak
    cv.line(x + 44, y + 8, x + 78, y + 66, RED, 3)
    burst(cv, x + 66, y + 92, 12, ORANGE)
    burst(cv, x + 84, y + 72, 9, ORANGE)


def pic_jet(cv, x, y):
    """Fighter jet on a dashed patrol path, rising to the right."""
    for i in range(0, 96, 12):                   # dashed path
        cv.line(x + 6 + i, y + 96 - i // 2, x + 12 + i, y + 93 - i // 2, BLUE, 2)
    cv.fill_poly([(x + 30, y + 78), (x + 96, y + 30), (x + 100, y + 38),
                  (x + 44, y + 84)], INK)       # fuselage
    cv.fill_poly([(x + 46, y + 66), (x + 70, y + 44), (x + 76, y + 52),
                  (x + 56, y + 74)], INK)       # wing
    cv.fill_poly([(x + 34, y + 82), (x + 52, y + 88), (x + 50, y + 94),
                  (x + 36, y + 90)], INK)       # tail wing
    cv.circle(x + 92, y + 32, 4, RED, fill=True)  # nose light
    cv.rect(x + 8, y + 108, 20, 3, BLUE)         # sea line
    cv.rect(x + 90, y + 108, 24, 3, BLUE)


def pic_parliament(cv, x, y):
    """Parliament building with columns and a flag; a resignation."""
    cv.rect(x + 14, y + 96, 92, 8, INK)          # steps
    cv.rect(x + 22, y + 88, 76, 8, INK)
    cv.rect(x + 30, y + 44, 60, 44, INK)         # hall
    cv.fill_poly([(x + 26, y + 44), (x + 60, y + 20), (x + 94, y + 44)], INK)
    for cx in (36, 50, 64, 78):                  # columns
        cv.rect(x + cx, y + 52, 6, 36, PAPER)
    cv.rect(x + 58, y + 8, 3, 16, INK)           # flag pole
    cv.fill_poly([(x + 61, y + 8), (x + 84, y + 13), (x + 61, y + 18)], RED)
    cv.line(x + 20, y + 112, x + 100, y + 112, GREY, 2)


def pic_virus(cv, x, y):
    """Spiky virus ball with a red cross badge."""
    cx, cy = x + 52, y + 58
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                   (1, 1), (-1, -1), (1, -1), (-1, 1),
                   (1, 0), (0, 1)):
        cv.line(cx, cy, cx + dx * 34, cy + dy * 34, RED, 3)
    cv.circle(cx, cy, 24, RED, fill=True)
    cv.circle(cx, cy, 24, INK)
    cv.circle(cx - 8, cy - 8, 5, WHITE, fill=True)
    cv.circle(cx + 9, cy + 7, 4, WHITE, fill=True)
    cv.rect(x + 88, y + 84, 26, 26, WHITE)       # cross badge
    cv.rect(x + 88, y + 84, 26, 26, INK)
    cv.rect(x + 98, y + 88, 6, 18, RED)
    cv.rect(x + 92, y + 94, 18, 6, RED)


def pic_crash(cv, x, y):
    """Plane diving, smoke plume, ground line."""
    cv.fill_poly([(x + 24, y + 34), (x + 78, y + 74), (x + 72, y + 82),
                  (x + 22, y + 44)], INK)       # fuselage
    cv.fill_poly([(x + 44, y + 52), (x + 58, y + 30), (x + 66, y + 36),
                  (x + 54, y + 58)], INK)       # wing
    cv.fill_poly([(x + 26, y + 36), (x + 14, y + 28), (x + 20, y + 26),
                  (x + 32, y + 32)], INK)       # tail
    cv.circle(x + 84, y + 84, 8, GREY, fill=True)   # smoke
    cv.circle(x + 96, y + 76, 11, GREY, fill=True)
    cv.circle(x + 104, y + 64, 7, GREY, fill=True)
    burst(cv, x + 92, y + 92, 14, ORANGE)
    cv.rect(x + 6, y + 108, 108, 4, INK)         # ground


def pic_globe(cv, x, y):
    """Globe with three stars: three leaders meeting in Shenzhen."""
    cv.circle(x + 60, y + 66, 34, BLUE)
    cv.circle(x + 60, y + 66, 34, INK)
    cv.line(x + 26, y + 66, x + 94, y + 66, BLUE, 2)
    cv.line(x + 60, y + 32, x + 60, y + 100, BLUE, 2)
    cv.line(x + 34, y + 44, x + 86, y + 44, BLUE, 2)
    cv.line(x + 34, y + 88, x + 86, y + 88, BLUE, 2)
    for sx, sy in ((30, 16), (60, 8), (90, 16)):
        burst(cv, x + sx, y + sy, 7, GOLD)
    cv.rect(x + 30, y + 108, 60, 3, INK)


def pic_house(cv, x, y):
    """A house with a cracked wall and a warning triangle."""
    cv.fill_poly([(x + 16, y + 62), (x + 60, y + 28), (x + 104, y + 62)], INK)
    cv.rect(x + 24, y + 62, 72, 44, INK)
    cv.rect(x + 30, y + 68, 60, 32, PAPER)       # wall face
    cv.line(x + 44, y + 68, x + 52, y + 84, RED, 3)   # crack
    cv.line(x + 52, y + 84, x + 46, y + 100, RED, 3)
    cv.rect(x + 52, y + 82, 16, 18, INK)         # door
    cv.fill_poly([(x + 88, y + 14), (x + 108, y + 44), (x + 68, y + 44)], GOLD)
    cv.fill_poly([(x + 88, y + 14), (x + 108, y + 44), (x + 68, y + 44)], INK)
    cv.fill_poly([(x + 92, y + 20), (x + 104, y + 40), (x + 76, y + 40)], GOLD)
    cv.rect(x + 86, y + 24, 4, 12, INK)
    cv.rect(x + 86, y + 38, 4, 4, INK)


# ------------------------------------------------------------------ stories
# (tag, tag colour, headline, subline, pictogram)
STORIES = [
    ("UKRAINE", RED, "KERCH BRIDGE HIT",
     "Ukraine strike partly collapses the bridge to Crimea; road and rail halted.",
     pic_bridge),
    ("UKRAINE", RED, "KYIV BRIDGES HIT",
     "Russian missiles damage two bridges in Kyiv; both crossings shut at first.",
     pic_kyiv),
    ("ASIA", BLUE, "JETS SCRAMBLED",
     "Suspected Russian planes enter Japan's airspace; Tokyo lodges a stern protest.",
     pic_jet),
    ("ASIA", GREEN, "MONGOLIA CHIEF QUITS",
     "President Khurelsukh resigns over graft claims; he denies wrongdoing.",
     pic_parliament),
    ("HEALTH", PURPLE, "MEASLES STATUS LOST",
     "US loses measles elimination status after 26 years; over 5,400 cases.",
     pic_virus),
    ("RUSSIA", INK, "PLANE CRASH KILLS 19",
     "Russian military plane crashes in the Kemerovo region; all aboard dead.",
     pic_crash),
    ("DIPLOMACY", TEAL, "APEC OPENS IN SHENZHEN",
     "Xi opens the summit; Trump, Xi and Putin set for first three-way talks.",
     pic_globe),
    ("WEST BANK", BROWN, "WOMAN, 72, SHOT DEAD",
     "Israeli settlers shoot a Palestinian woman near Jericho, ministry says.",
     pic_house),
]


def draw_panel(cv, x, y, w, h, story):
    tag, color, headline, sub, pic = story
    cv.rect(x, y, w, h, WHITE)
    cv.rect(x, y, w, h, INK)               # border (drawn as outline below)
    cv.rect(x + 2, y + 2, w - 4, h - 4, WHITE)
    cv.rect(x, y, w, 26, color)            # tag band
    cv.text(x + 10, y + 6, tag, 2, WHITE)
    # pictogram in a tinted square on the left (border, then tinted fill)
    px, py = x + 12, y + 38
    cv.rect(px, py, 120, 120, INK)
    cv.rect(px + 2, py + 2, 116, 116, LIGHT)
    pic(cv, px + 2, py + 2)
    # headline + subline on the right
    tx = px + 120 + 14
    tw = x + w - 12 - tx
    yy = y + 40
    for ln in wrap_text(headline, tw, 3):
        cv.text(tx, yy, ln, 3, INK)
        yy += 7 * 3 + 4
    yy += 4
    cv.para(tx, yy, sub, 2, GREY, tw, line_gap=4)


def build():
    cv = Canvas(W, H, PAPER)
    # ---- masthead
    cv.text_center(W // 2, 26, "WORLD NEWS", 9, INK)
    cv.hline(24, 118, W - 48, RED, 5)
    cv.hline(24, 128, W - 48, INK, 2)
    # ---- date line: the day this page sums up
    cv.text_center(W // 2, 146, "TUESDAY, 17 NOVEMBER 2026", 4, RED)
    cv.text_center(W // 2, 182, "EIGHT STORIES FROM AROUND THE WORLD", 2, INK)
    # ---- story grid: 2 columns x 4 rows
    gx, gy = 24, 206
    pw = (W - 2 * 24 - 12) // 2
    ph = 186
    for i, story in enumerate(STORIES):
        col = i % 2
        row = i // 2
        draw_panel(cv, gx + col * (pw + 12), gy + row * (ph + 10),
                   pw, ph, story)
    # ---- footer
    cv.text_center(W // 2, 990, "ALL EVENTS REPORTED ON 17 NOVEMBER 2026", 2, GREY)
    return cv


# ---------------------------------------------------------------- PNG writer
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(build())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
