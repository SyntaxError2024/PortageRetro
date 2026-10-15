# Zorgon's Revenge (Oric, 1984) - le jeu en Python

Le code machine 6502 d'origine est **traduit automatiquement en Python** (une fonction par bloc d'instructions,
l'instruction d'origine en commentaire sur chaque ligne), puis exécuté par un petit moteur. La logique du jeu
(héros, ascenseur, monstres, cloches, score, menus, les 4 missions) est donc celle de l'original, à la vitesse
exacte de l'Oric.

## Jouer
    pip install pygame-ce
    python play.py

| Touche | Action |
|---|---|
| flèches gauche / droite | courir (missions 1, 3, 4) |
| espace ou flèche haut | sauter ; valider dans les menus |
| flèche haut / flèche bas | **mission 2 (vaisseau) : monter / descendre** ; espace = tirer |
| 1 2 3 4 | choisir la mission (le jeu tire au hasard laquelle se lance) |
| Tab | « Esc » du jeu (retour au menu) |
| S | musique originale (puce AY) / arrangée (instruments) |
| Échap | quitter |

Aucune cassette n'est nécessaire.

## Les fichiers
| Fichier | Rôle |
|---|---|
| `play.py` | programme principal : fenêtre pygame, touches, son |
| `core.py` | le moteur : exécute les blocs traduits, remplace le clavier, la puce sonore et le BASIC du chargeur |
| `game_code.py` | **le code du jeu traduit en Python** (généré, 2 510 blocs, 10 870 instructions) |
| `memory_image.hex` | la mémoire de l'Oric après chargement, en hexadécimal commenté : graphismes, textes, tables, musique |
| `screen.py`, `font6x8.py` | affichage : lit le tampon écran du jeu (octets de 6 pixels + attributs de couleur) et le dessine |
| `sound.py`, `music_data.py` | son : 3 mélodies en hexadécimal commenté (versions originale et arrangée) + effets lus dans les registres de la puce AY |
| `tools/` | traducteur (`recompile.py`), test de comparaison avec l'émulateur (`lockstep.py`), outils d'analyse |
| `version_manuelle/` | ma première version, portée à la main (héros, ascenseur, mission 3 seulement, sprites en PNG) : conservée comme référence lisible |

## Vérification
`python tools/lockstep.py 200000` exécute le code traduit et un émulateur 6502 côte à côte, bloc par bloc, et
compare les registres à chaque bloc et toute la mémoire régulièrement. Résultat : 2,6 millions de blocs identiques
sur chacune des 4 missions, avec des touches aléatoires.

## Limites connues
- La musique « temps réel » du chargeur BASIC (`GOSUB 200`) n'est pas jouée (le jeu continue sans elle).
- Les 3 lignes de texte du bas utilisent une police 6x8 de remplacement (la ROM de l'Oric n'est pas sur la cassette).
- Le son n'a pas été écouté : le synthétiseur de la puce AY est vérifié par mesure de fréquence, pas à l'oreille.
- Les graphismes viennent de la mémoire d'origine (octets de pixels) : les PNG de `version_manuelle/` ne sont pas utilisés ici.

Le code et les données de ce dossier proviennent de la cassette d'origine (Severn Software, 1984) : usage personnel.
