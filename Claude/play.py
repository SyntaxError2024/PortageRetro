"""
play.py - jouer à Zorgon's Revenge (Oric, 1984) : le code d'origine, traduit automatiquement en Python.

    pip install pygame-ce
    python play.py

Missions 1, 3 et 4 : flèches gauche/droite = courir, espace ou flèche haut = sauter.
Mission 2 (vaisseau) : flèche haut = monter, flèche bas = descendre, espace = tirer.
1 2 3 4 = choisir la mission, espace = valider, Tab = « Esc » du jeu (retour au menu),
S = musique originale / arrangée, Échap = quitter.

Le jeu tourne à la vitesse exacte de l'Oric : 20 000 cycles de processeur par image (1 MHz, 50 Hz).
"""
import os
import sys
import pygame
import core
from screen import Renderer, W, H
from sound import Sound

HERE = os.path.dirname(os.path.abspath(__file__))
CYCLES_PER_FRAME = 20000
FPS = 50
ZOOM = 3

# touche -> (ligne, masque colonne) de la matrice clavier de l'Oric, tels que le jeu les teste.
# Les mêmes cellules de la matrice servent à des choses différentes selon la mission :
#   (4,$FE) espace : sauter (héros) / tirer (vaisseau) / valider    (4,$DF) : gauche (héros) / DESCENDRE (vaisseau)
#   (4,$BF) : droite (héros)                                        (0,$BF) : MONTER (vaisseau, mission 2)
KEYS_COMMON = {
    pygame.K_SPACE: (4, 0xFE),
    pygame.K_1: (0, 0xDF), pygame.K_2: (2, 0xBF), pygame.K_3: (0, 0x7F), pygame.K_4: (2, 0xF7),   # choix de la mission
    pygame.K_TAB: (1, 0xDF),                                                                       # Esc du jeu
}
KEYS_HERO = {pygame.K_UP: (4, 0xFE), pygame.K_LEFT: (4, 0xDF), pygame.K_RIGHT: (4, 0xBF)}          # missions 1, 3 et 4
KEYS_SHIP = {pygame.K_UP: (0, 0xBF), pygame.K_DOWN: (4, 0xDF)}                                    # mission 2 : le vaisseau


def keymap(machine):
    """Le vaisseau de la mission 2 se pilote avec haut/bas ; dans les autres missions on court et on saute."""
    return {**KEYS_COMMON, **(KEYS_SHIP if machine.m[0x411] == 2 else KEYS_HERO)}


MELODY_NAMES = {0x787B: "debut_partie", 0x78C7: "melodie_b", 0x77D5: "fanfare"}


def load_image(path=os.path.join(HERE, "memory_image.hex")):
    """Lit memory_image.hex (lignes « ADRESSE: octets » ; les lignes # sont des commentaires)."""
    mem = bytearray(65536)
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        addr, data = line.split(":")
        b = bytes.fromhex(data.replace(" ", ""))
        a = int(addr, 16)
        mem[a:a + len(b)] = b
    return mem


def main():
    pygame.init()
    window = pygame.display.set_mode((W * ZOOM, H * ZOOM))
    pygame.display.set_caption("Zorgon's Revenge")
    machine = core.Machine(load_image())
    renderer = Renderer()
    snd = Sound(volume=8, style="original")
    print("son :", "actif" if snd.ok else f"désactivé ({snd.error})")
    snd.prepare()
    clock = pygame.time.Clock()
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_s:
                print("style de la musique :", snd.toggle_style())
        pressed = pygame.key.get_pressed()
        machine.set_keys({mk for pk, mk in keymap(machine).items() if pressed[pk]})
        machine.run(CYCLES_PER_FRAME)                         # une image de jeu
        for ev in machine.events:                             # événements du chargeur BASIC : musique
            if ev[0] == "melody" and ev[1] in MELODY_NAMES:
                snd.volume = max(4, min(15, 4 + 2 * ev[3]))   # volume choisi dans le menu du jeu ($04FD)
                snd.play_melody(MELODY_NAMES[ev[1]])
        machine.events.clear()
        snd.feed_ay(machine.ay)                               # effets sonores : registres de la puce AY
        surf = pygame.image.frombuffer(renderer.update(machine.m), (W, H), "RGB").convert()   # même format que l'écran
        window.blit(pygame.transform.scale(surf, window.get_size()), (0, 0))
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    main()
