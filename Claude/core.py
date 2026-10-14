"""
core.py - le « moteur » qui fait tourner game_code.py (le code 6502 traduit en Python).

Machine : mémoire de 64 Ko, registres, pile d'appels, compteur de cycles. run(budget) exécute des blocs
jusqu'à épuisement du budget de cycles (1 image = 20 000 cycles à 1 MHz / 50 Hz) : la vitesse du jeu est donc
exactement celle de l'Oric, sans réglage. Les routines qui parlent au matériel (clavier, puce sonore) et le
mini-BASIC du chargeur (modes écran, musique) sont remplacés par des fonctions Python.
"""
import game_code

SCREEN, SCREEN_END = 0xA000, 0xBF40            # écran HIRES : 40 octets x 200 lignes
TEXT, TEXT_END = 0xBF68, 0xC000                # 3 lignes de texte sous l'écran HIRES
SENTINEL = -1                                  # adresse de retour « vers le BASIC »


class Machine:
    def __init__(self, image, seed=1):
        self.m = bytearray(image)              # mémoire (copie)
        self.a = self.x = self.y = 0
        self.C = self.Z = self.N = self.V = 0
        self.stack = []                        # pile des adresses de retour (JSR/RTS)
        self.stack_data = []                   # PHA/PLA
        self.cycles = 0
        self.keys = set()                      # touches enfoncées : (ligne, masque colonne) de la matrice Oric
        self.latch = (0, 0)                    # (PB, PA) laissés par le balayage clavier de l'IRQ de la ROM
        self.ay = [0] * 16                     # registres de la puce sonore
        self.events = []                       # événements pour le son : ("melody", adresse), ...
        self.hires = False
        self.rng = seed
        self.m[0], self.m[1] = 0x13, 0x07      # BASIC ligne 10 : DOKE 0,#713
        self.pc = self.basic_step()            # ligne 5 : HIRES, puis CALL DEEK(0)

    # ------------------------------------------------------------ entrées/sorties
    def random(self):
        """Octet pseudo-aléatoire (le jeu lit le compteur du timer VIA $0308 comme générateur aléatoire)."""
        self.rng = (self.rng * 1103515245 + 12345) & 0x7FFFFFFF
        return (self.rng >> 16) & 0xFF

    def io_read(self, addr):
        if addr == 0x0300: return self.latch[0]
        if addr == 0x0301: return self.latch[1]
        if addr in (0x0304, 0x0308): return self.random()
        return 0

    def set_keys(self, keys):
        """Met à jour les touches et le « dernier code de touche » que l'IRQ de la ROM laisse dans le VIA :
        PB = $B8 | ligne, PA = masque de colonne de la touche enfoncée."""
        self.keys = set(keys)
        self.latch = (0, 0)
        for row, mask in sorted(self.keys):
            self.latch = (0xB8 | row, mask)
            break

    # ------------------------------------------------------------ le mini-BASIC du chargeur (lignes 5-250)
    def basic_step(self):
        """Ce que fait le BASIC quand le code machine lui rend la main : selon le drapeau en $03 il change de
        mode écran ou joue de la musique, puis il rappelle le code à l'adresse en $00/$01."""
        m = self.m
        flag = m[3]
        if flag == 2 or (flag == 0 and not self.hires and self.cycles == 0):     # HIRES : efface l'écran
            self.hires = True
            for i in range(SCREEN, SCREEN_END): m[i] = 0x40
            for i in range(TEXT, TEXT_END): m[i] = 0x20
        elif flag == 1:
            self.hires = False                                                 # TEXT
        elif flag == 3:                                                        # GOSUB 100 : mélodie en mémoire
            self.events.append(("melody", m[4] | m[5] << 8, m[6], m[0x4FD]))
        elif flag == 4:                                                        # GOSUB 200 : musique temps réel
            self.events.append(("music_rt", m[0x4FD]))
        self.stack.append(SENTINEL)
        return m[0] | m[1] << 8                                                # CALL DEEK(0)

    # ------------------------------------------------------------ exécution
    def run(self, budget):
        limit = self.cycles + budget
        blocks, hooks = game_code.BLOCKS, HOOKS
        pc = self.pc
        while self.cycles < limit:
            if pc < 0:
                pc = self.basic_step(); continue
            f = hooks.get(pc)
            if f is not None:
                f(self); self.cycles += 24
                pc = self.stack.pop() if self.stack else SENTINEL
                continue
            b = blocks.get(pc)
            if b is None:
                raise RuntimeError(f"bloc inconnu ${pc:04X}")
            pc = b(self)
        self.pc = pc


# ---------------------------------------------------------------- routines matérielles remplacées
def hook_keytest(c):
    """[$5FDE] A = ligne, X = masque de colonne : touche enfoncée -> A = 8 (bit 3 de $0300), sinon 0."""
    down = (c.a & 7, c.x) in c.keys
    c.a = 8 if down else 0
    c.Z = int(not down); c.N = 0

def hook_ay_write(c):
    """[$5456] écrit Y dans le registre X de la puce sonore ; le jeu garde une copie du mélangeur en $6101."""
    c.ay[c.x & 15] = c.y
    if c.x == 7:
        c.m[0x6101] = c.y

def hook_ay_voice(c):
    """[$5482] règle la période de la voix $03 (1 à 3) avec $04/$05 ; la voix 4 est le bruit. Décrémente $03."""
    m = c.m
    m[3] = (m[3] - 1) & 0xFF
    ch = m[3]
    if ch < 3:
        c.ay[2 * ch] = m[4]; c.ay[2 * ch + 1] = m[5]
        c.x = 2 * ch + 1; c.y = m[5]
    else:
        c.ay[6] = m[4]; c.x = 6; c.y = m[4]
    c.a = 0; c.Z = 1; c.N = 0

def hook_ay_init(c):
    """[$54AC] mélangeur = $FF (tout coupé), volumes des 3 voix = [$04FD]."""
    c.ay[7] = 0xFF; c.m[0x6101] = 0xFF
    for r in (8, 9, 10): c.ay[r] = c.m[0x4FD]
    c.x = 11; c.y = c.m[0x4FD]; c.Z = 1; c.C = 1; c.N = 0


HOOKS = {0x5FDE: hook_keytest, 0x5456: hook_ay_write, 0x5482: hook_ay_voice, 0x54AC: hook_ay_init}
