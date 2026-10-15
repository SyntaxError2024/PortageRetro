"""
screen.py - AFFICHAGE : transforme le tampon écran du jeu en image, comme le fait l'Oric.

Le code du jeu (game_code.py) écrit ses graphismes dans la mémoire écran HIRES ($A000-$BF3F, 40 octets x 200
lignes). Ici on lit ce tampon et on le dessine :
  - un octet >= $40 = 6 pixels (bit 5 à gauche) ; le bit 7 inverse l'encre et le papier ;
  - un octet < $20 = ATTRIBUT : 0-7 change l'encre, 16-23 change le papier jusqu'à la fin de la ligne ; il occupe
    lui-même une cellule de 6 pixels à la couleur du papier ;
  - au début de chaque ligne : encre blanche, papier noir.
Les 3 lignes de texte du bas ($BF68) utilisent la police 6x8 de font6x8.py.
Seules les lignes modifiées depuis la dernière image sont redessinées.
"""
from font6x8 import GLYPHS

SCREEN, TEXT = 0xA000, 0xBF68
W, H_HIRES, TEXT_ROWS = 240, 200, 3
H = H_HIRES + TEXT_ROWS * 8
PAL = [(0, 0, 0), (255, 0, 0), (0, 255, 0), (255, 255, 0), (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255)]
_PX = {}


def _cell(b, ink, paper):
    """18 octets RGB (6 pixels) d'un octet de pixels."""
    k = (b, ink, paper)
    r = _PX.get(k)
    if r is None:
        fg, bg = (paper, ink) if b & 0x80 else (ink, paper)
        r = _PX[k] = b"".join(bytes(PAL[fg if b & (0x20 >> i) else bg]) for i in range(6))
    return r


def hires_row(m, y):
    """720 octets RGB de la ligne `y` (0-199) de l'écran HIRES."""
    ink, paper = 7, 0
    out = bytearray()
    base = SCREEN + y * 40
    for cx in range(40):
        b = m[base + cx]
        if b & 0x60 == 0:                                   # attribut
            k = b & 0x1F
            if k < 8:
                ink = k
            elif 16 <= k < 24:
                paper = k - 16
            out += _cell(0x40, ink, paper)                  # cellule vide à la couleur du papier
        else:
            out += _cell(b, ink, paper)
    return bytes(out)


def text_rows(m, r):
    """8 lignes de 720 octets RGB pour la ligne de texte `r` (0-2)."""
    ink, paper = 7, 0
    rows = [bytearray() for _ in range(8)]
    base = TEXT + r * 40
    for cx in range(40):
        b = m[base + cx]
        if b & 0x60 == 0:                                   # attribut de texte
            k = b & 0x1F
            if k < 8:
                ink = k
            elif 16 <= k < 24:
                paper = k - 16
            glyph = (0,) * 8
            inv = 0
        else:
            glyph = GLYPHS.get(b & 0x7F, (0,) * 8)
            inv = b & 0x80
        fg, bg = (paper, ink) if inv else (ink, paper)
        for y in range(8):
            g = glyph[y]
            rows[y] += b"".join(bytes(PAL[fg if g & (0x20 >> i) else bg]) for i in range(6))
    return [bytes(r_) for r_ in rows]


class Renderer:
    """Garde l'image RVB complète (240 x 224) et ne met à jour que les lignes qui ont changé."""
    def __init__(self):
        self.frame = bytearray(W * H * 3)
        self._prev = [None] * H_HIRES
        self._prev_text = [None] * TEXT_ROWS

    def update(self, m):
        f = self.frame
        for y in range(H_HIRES):
            base = SCREEN + y * 40
            cur = bytes(m[base:base + 40])
            if cur != self._prev[y]:
                self._prev[y] = cur
                f[y * 720:(y + 1) * 720] = hires_row(m, y)
        for r in range(TEXT_ROWS):
            base = TEXT + r * 40
            cur = bytes(m[base:base + 40])
            if cur != self._prev_text[r]:
                self._prev_text[r] = cur
                for i, row in enumerate(text_rows(m, r)):
                    y = H_HIRES + r * 8 + i
                    f[y * 720:(y + 1) * 720] = row
        return self.frame
