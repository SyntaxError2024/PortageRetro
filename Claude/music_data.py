"""
music_data.py - GÉNÉRÉ par tools/export_assets.py : les 3 mélodies de la cassette, en hexadécimal.

Chaque note = 2 octets : (hauteur, durée).
  hauteur : NN = hauteur - 5 ; octave Oric = NN // 48 + 2 ; note = ((NN % 48) / 4 + 1.5) tronqué, 1 = Do ... 12 = Si
            (le BASIC du chargeur, lignes 120-130, joue MUSIC 1, octave, note, volume)
  durée   : nombre d'unités de temps (le BASIC attend durée x 18 tours de boucle, ligne 135)
Le commentaire de chaque ligne donne la note en octave scientifique (octave Oric + 1, le La 440 Hz = La4).
"""


# $787B, 38 notes, jouée en $07A9, avant l'écran de sélection de mission
MELODIE_DEBUT_PARTIE = [
    # (hauteur, durée)   note
    (0x7D, 0x01),  # Fa#5, durée 1
    (0x81, 0x04),  # Sol5, durée 4
    (0x75, 0x04),  # Mi5, durée 4
    (0x75, 0x04),  # Mi5, durée 4
    (0x75, 0x03),  # Mi5, durée 3
    (0x7D, 0x01),  # Fa#5, durée 1
    (0x81, 0x04),  # Sol5, durée 4
    (0x75, 0x04),  # Mi5, durée 4
    (0x75, 0x04),  # Mi5, durée 4
    (0xA5, 0x04),  # Mi6, durée 4
    (0x9D, 0x02),  # Ré6, durée 2
    (0x95, 0x02),  # Do6, durée 2
    (0x91, 0x02),  # Si5, durée 2
    (0x89, 0x02),  # La5, durée 2
    (0x81, 0x04),  # Sol5, durée 4
    (0x79, 0x04),  # Fa5, durée 4
    (0x75, 0x04),  # Mi5, durée 4
    (0x79, 0x04),  # Fa5, durée 4
    (0x81, 0x07),  # Sol5, durée 7
    (0x7D, 0x01),  # Fa#5, durée 1
    (0x81, 0x04),  # Sol5, durée 4
    (0x75, 0x04),  # Mi5, durée 4
    (0x75, 0x04),  # Mi5, durée 4
    (0x75, 0x03),  # Mi5, durée 3
    (0x7D, 0x01),  # Fa#5, durée 1
    (0x81, 0x04),  # Sol5, durée 4
    (0x75, 0x04),  # Mi5, durée 4
    (0x75, 0x04),  # Mi5, durée 4
    (0xA5, 0x04),  # Mi6, durée 4
    (0x9D, 0x02),  # Ré6, durée 2
    (0x95, 0x02),  # Do6, durée 2
    (0x91, 0x02),  # Si5, durée 2
    (0x89, 0x02),  # La5, durée 2
    (0x81, 0x04),  # Sol5, durée 4
    (0x91, 0x04),  # Si5, durée 4
    (0x95, 0x04),  # Do6, durée 4
    (0xA5, 0x04),  # Mi6, durée 4
    (0x95, 0x04),  # Do6, durée 4
]

# $78C7, 24 notes, jouée en $08D6 (contexte à confirmer : échec ou fin de mission)
MELODIE_B = [
    # (hauteur, durée)   note
    (0x79, 0x06),  # Fa5, durée 6
    (0x89, 0x02),  # La5, durée 2
    (0x95, 0x04),  # Do6, durée 4
    (0xA9, 0x04),  # Fa6, durée 4
    (0xB9, 0x04),  # La6, durée 4
    (0xB1, 0x04),  # Sol6, durée 4
    (0xA9, 0x04),  # Fa6, durée 4
    (0x9D, 0x04),  # Ré6, durée 4
    (0x91, 0x04),  # Si5, durée 4
    (0x95, 0x0C),  # Do6, durée 12
    (0x95, 0x08),  # Do6, durée 8
    (0x79, 0x06),  # Fa5, durée 6
    (0x89, 0x02),  # La5, durée 2
    (0x95, 0x04),  # Do6, durée 4
    (0xA9, 0x04),  # Fa6, durée 4
    (0xB9, 0x04),  # La6, durée 4
    (0xB1, 0x04),  # Sol6, durée 4
    (0xA9, 0x04),  # Fa6, durée 4
    (0x9D, 0x04),  # Ré6, durée 4
    (0x95, 0x04),  # Do6, durée 4
    (0x8D, 0x04),  # La#5, durée 4
    (0x89, 0x04),  # La5, durée 4
    (0x81, 0x04),  # Sol5, durée 4
    (0x79, 0x08),  # Fa5, durée 8
]

# $77D5, 35 notes, jouée en $0974, juste avant l'écran final $4600
FANFARE = [
    # (hauteur, durée)   note
    (0x95, 0x08),  # Do6, durée 8
    (0x91, 0x06),  # Si5, durée 6
    (0x81, 0x02),  # Sol5, durée 2
    (0x89, 0x04),  # La5, durée 4
    (0x81, 0x04),  # Sol5, durée 4
    (0x79, 0x04),  # Fa5, durée 4
    (0x6D, 0x04),  # Ré5, durée 4
    (0x65, 0x04),  # Do5, durée 4
    (0x61, 0x02),  # Si4, durée 2
    (0x65, 0x02),  # Do5, durée 2
    (0x6D, 0x04),  # Ré5, durée 4
    (0x51, 0x02),  # Sol4, durée 2
    (0x6D, 0x02),  # Ré5, durée 2
    (0x75, 0x04),  # Mi5, durée 4
    (0x51, 0x02),  # Sol4, durée 2
    (0x65, 0x02),  # Do5, durée 2
    (0x75, 0x02),  # Mi5, durée 2
    (0x81, 0x02),  # Sol5, durée 2
    (0x89, 0x02),  # La5, durée 2
    (0x91, 0x02),  # Si5, durée 2
    (0x95, 0x08),  # Do6, durée 8
    (0x91, 0x06),  # Si5, durée 6
    (0x81, 0x02),  # Sol5, durée 2
    (0x89, 0x04),  # La5, durée 4
    (0x81, 0x04),  # Sol5, durée 4
    (0x79, 0x04),  # Fa5, durée 4
    (0x6D, 0x04),  # Ré5, durée 4
    (0x65, 0x04),  # Do5, durée 4
    (0x61, 0x02),  # Si4, durée 2
    (0x65, 0x02),  # Do5, durée 2
    (0x75, 0x04),  # Mi5, durée 4
    (0x6D, 0x02),  # Ré5, durée 2
    (0x75, 0x02),  # Mi5, durée 2
    (0x6D, 0x08),  # Ré5, durée 8
    (0x65, 0x08),  # Do5, durée 8
]

MELODIES = {
    "debut_partie": MELODIE_DEBUT_PARTIE,
    "melodie_b": MELODIE_B,
    "fanfare": FANFARE,
}
