"""
sound.py - le SON de Zorgon's Revenge, sans fichier audio : tout est synthétisé.

La puce sonore de l'Oric (AY-3-8912) produit des ondes carrées. Le jeu règle sa période sur 12 bits
([$5482] : $04 = octet bas, $05 = octet haut, $03 = voix 1..3) et la fréquence vaut
        f = 1 000 000 / (16 x période)                                   (horloge AY de l'Oric : 1 MHz)

Deux sources de sons dans le jeu d'origine :
  - les MÉLODIES : tables de paires (hauteur, durée) de la cassette ($77D5, $787B, $78C7), dans music_data.py, jouées par la
    commande BASIC MUSIC (lignes 100-135 du chargeur) ;
  - les EFFETS : le code 6502 règle directement la période (saut [$1150], mort [$139B], pas [$1138]).

DEUX STYLES pour les mélodies (même notes, même tempo) :
  "original" : ondes carrées de la puce AY, comme sur l'Oric ;
  "arrange"  : version harmonisée avec des instruments (piano, cordes, basse) : tonalité détectée,
               accords choisis d'après la mélodie, accompagnement ajouté. Les effets (saut, mort) restent
               en son d'origine dans les deux styles.

pygame n'est utilisé QUE pour jouer les échantillons. S'il est absent, ou s'il n'y a pas de carte son,
le jeu fonctionne en silence (aucune erreur).
"""
import array
import math
import wave

RATE = 22050
AY_CLOCK = 1_000_000

# ---- RÉGLAGES (hauteur et tempo validés à l'oreille par l'utilisateur) -------------------------------
OCT_OFFSET = 1          # octave scientifique = octave MUSIC de l'Oric + OCT_OFFSET
SEC_PER_UNIT = 0.027    # durée d'une unité de durée : le BASIC attend D x 18 tours de boucle FOR..NEXT [$0135]
JUMP_TICK_S = 0.020     # durée estimée d'un tour du héros pour le glissando du saut (non mesurée)

# ---- les 3 mélodies sont dans music_data.py (hexadécimal commenté) -------------------------------------
from music_data import MELODIES as RAW_MELODIES


def load_melodies():
    """Décode les paires d'octets (hauteur, durée) comme le fait le BASIC du chargeur (lignes 120-130) :
         NN = hauteur - 5 ;  O = NN / 48 ;  octave = INT(O) + 2 ;  note = INT((O - INT(O)) * 12 + 1.5)
       Retourne {nom: [(octave, note, durée), ...]}."""
    out = {}
    for name, pairs in RAW_MELODIES.items():
        notes = []
        for pitch, duration in pairs:
            nn = pitch - 5
            o = nn / 48
            octave = int(o) + 2
            note = int((o - int(o)) * 12 + 1.5)
            if note > 12:                      # 13 : on passe à l'octave suivante
                note -= 12; octave += 1
            notes.append((octave, note, duration))
        out[name] = notes
    return out


def note_freq(octave, note):
    """Fréquence en Hz. note 1 = do ... 12 = si ; le la de 440 Hz est la note 10 de l'octave scientifique 4."""
    return 261.6256 * 2 ** ((octave + OCT_OFFSET - 4) + (note - 1) / 12)


def period_to_freq(period):
    """Période AY 12 bits -> Hz."""
    return AY_CLOCK / (16 * max(1, period))


# ---------------------------------------------------------------- synthèse (bibliothèque standard)
def square(freq, seconds, amp):
    """Onde carrée mono 16 bits, sous forme de array('h')."""
    n = int(RATE * seconds)
    half = max(1.0, RATE / freq / 2)
    a = int(32767 * amp)
    return array.array("h", (a if int(i / half) % 2 == 0 else -a for i in range(n)))


def volume_to_amp(v):
    """Volume AY 0..15 ($04FD dans le jeu) -> amplitude 0..0.5."""
    return 0.5 * max(0, min(15, v)) / 15


def melody_samples(notes, volume=8):
    out = array.array("h")
    for octave, note, d in notes:
        out.extend(square(note_freq(octave, note), d * SEC_PER_UNIT, volume_to_amp(volume)))
    return out


def jump_samples(volume=8, tick_s=JUMP_TICK_S, fall_ticks=100):
    """Son du saut, une tonalité par TOUR du héros (voix 1 de la puce AY).
    Départ [$119F] : période 150. Ensuite, à chaque tour du héros [$1150] :
        compteur vertical >= 0 (montée, 21 tours)  ->  période - 5   (le son monte)
        compteur négatif (chute)                   ->  période + 5   (le son descend)
    Le son s'arrête à l'atterrissage [$1186] : on génère une chute assez longue (`fall_ticks`) et le jeu
    coupe le son à l'atterrissage (Sound.stop_jump). `tick_s` = durée d'un tour du héros en l'air
    (tick_reload / PASSES_PER_SECOND), pour que le son dure exactement comme le saut."""
    out, period, amp = array.array("h"), 150, volume_to_amp(volume)
    for k in range(21 + fall_ticks):
        period += -5 if k < 21 else 5
        out.extend(square(period_to_freq(period), tick_s, amp))
    return out


def death_samples(volume=8, segments=((24, 0.04),)):
    """Son de mort : voix 2, période $01E8 (488) au départ [$1360], +$32 (50) à chaque tour [$139B] :
    glissando descendant. `segments` = ((nombre de tours, durée d'un tour en secondes), ...) : pendant la
    chute un tour dure 15 tours de boucle, puis 30 après l'atterrissage [$12A7]."""
    out, period, amp = array.array("h"), 0x01E8, volume_to_amp(volume)
    for count, tick_s in segments:
        for _ in range(count):
            period += 0x32
            out.extend(square(period_to_freq(period), tick_s, amp))
    return out


# ================================================================ VERSION ARRANGÉE =====================
STYLES = ("original", "arrange")
WINDOW_UNITS = 16        # un accord par fenêtre de 16 unités de durée (~0,43 s)
REPEAT_PENALTY = 0.45    # malus (x durée de la fenêtre) quand le même accord se répète : évite une harmonie plate

MAJOR = [0, 2, 4, 5, 7, 9, 11]
MINOR = [0, 2, 3, 5, 7, 8, 10]                       # mineur naturel
_KS_MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]   # Krumhansl-Schmuckler
_KS_MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
NOTE_NAMES = ["do", "do#", "ré", "ré#", "mi", "fa", "fa#", "sol", "sol#", "la", "la#", "si"]


def midi(octave, note):
    """Numéro MIDI (do central = 60) de la note du jeu."""
    return 12 * (octave + OCT_OFFSET + 1) + (note - 1)


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def detect_key(notes):
    """Tonalité la plus probable (tonique 0..11, 'maj'/'min') d'après les durées des notes."""
    hist = [0.0] * 12
    for o, n, d in notes:
        hist[(n - 1) % 12] += d
    best = None
    for tonic in range(12):
        for mode, prof in (("maj", _KS_MAJOR), ("min", _KS_MINOR)):
            rot = [prof[(pc - tonic) % 12] for pc in range(12)]
            mh, mr = sum(hist) / 12, sum(rot) / 12
            num = sum((h - mh) * (r - mr) for h, r in zip(hist, rot))
            den = math.sqrt(sum((h - mh) ** 2 for h in hist) * sum((r - mr) ** 2 for r in rot)) or 1
            sc = num / den
            if best is None or sc > best[0]:
                best = (sc, tonic, mode)
    return best[1], best[2]


def triads(tonic, mode):
    """Les 7 accords de la gamme : liste de (degré, [fondamentale, tierce, quinte] en classes de hauteur)."""
    scale = [(tonic + i) % 12 for i in (MAJOR if mode == "maj" else MINOR)]
    return [(d, [scale[d], scale[(d + 2) % 7], scale[(d + 4) % 7]]) for d in range(7)]


def harmonize(notes):
    """Choisit un accord par fenêtre : celui qui contient le plus de notes de la mélodie (pondérées par
    leur durée), avec une préférence pour I, IV et V, et une fin sur l'accord de tonique."""
    tonic, mode = detect_key(notes)
    chords = triads(tonic, mode)
    total = sum(d for _, _, d in notes)
    nwin = max(1, -(-total // WINDOW_UNITS))
    wins = [[] for _ in range(nwin)]
    pos = 0
    for o, n, d in notes:
        wins[min(nwin - 1, pos // WINDOW_UNITS)].append(((n - 1) % 12, d))
        pos += d
    plan = []
    for w, ws in enumerate(wins):
        best = None
        wdur = sum(d for _, d in ws)
        for deg, pcs in chords:
            sc = 0.0
            for pc, d in ws:
                sc += d * (1.2 if pc == pcs[0] else 1.0) if pc in pcs else -0.5 * d
            sc += 0.3 * sum(d for _, d in ws) * (deg in (0, 3, 4))
            if w == nwin - 1 and deg == 0:           # cadence : on termine sur la tonique
                sc += 1e6
            if w == 0 and deg == 0:
                sc += 0.5 * sum(d for _, d in ws)
            if w >= 1 and plan[w - 1][0] == deg:
                sc -= REPEAT_PENALTY * wdur
            if w >= 2 and plan[w - 2][0] == deg:
                sc -= 0.5 * REPEAT_PENALTY * wdur
            if best is None or sc > best[0]:
                best = (sc, deg, pcs)
        plan.append((best[1], best[2]))
    return tonic, mode, plan


def _voice(buf, start_s, dur_s, freq, amp, harm, attack, release, tau=None, sustain=1.0, detune=0.0):
    """Ajoute une note (somme d'harmoniques, enveloppe attaque / déclin / relâchement) au tampon float."""
    i0, n = int(start_s * RATE), int(dur_s * RATE)
    two_pi = 2 * math.pi
    freqs = [freq] if not detune else [freq * (1 - detune), freq * (1 + detune)]
    norm = amp / len(freqs)
    for i in range(n):
        t = i / RATE
        env = min(1.0, t / attack) * min(1.0, (dur_s - t) / release)
        if tau:
            env *= sustain + (1 - sustain) * math.exp(-t / tau)
        if env <= 0:
            continue
        v = 0.0
        for f in freqs:
            ph = two_pi * f * t
            for k, a in enumerate(harm, 1):
                v += a * math.sin(k * ph)
        if i0 + i < len(buf):
            buf[i0 + i] += norm * env * v


def arrange_samples(notes, volume=8):
    """Mélodie arrangée : piano (mélodie) + cordes (accords) + basse, plus une légère réverbération."""
    tonic, mode, plan = harmonize(notes)
    unit = SEC_PER_UNIT
    total_s = sum(d for _, _, d in notes) * unit
    tail = 0.5
    buf = [0.0] * int((total_s + tail) * RATE)
    # --- mélodie : piano (harmoniques décroissantes, attaque vive, déclin avec résonance)
    t = 0.0
    for o, n, d in notes:
        dur = d * unit
        _voice(buf, t, dur + 0.12, midi_hz(midi(o, n)), 0.50, [1, .45, .30, .16, .10, .05],
               attack=0.004, release=0.10, tau=0.30, sustain=0.30)
        t += dur
    # --- accompagnement : un accord par fenêtre
    win_s = WINDOW_UNITS * unit
    for w, (deg, pcs) in enumerate(plan):
        start = w * win_s
        dur = min(win_s, total_s - start)
        if dur <= 0:
            break
        root, third, fifth = pcs
        r = 48 + root                                           # cordes : do2-si3 environ
        voicing = [r, r + (third - root) % 12, r + (fifth - root) % 12]
        for m in voicing:                                       # fond de cordes (2 oscillateurs désaccordés)
            _voice(buf, start, dur + 0.10, midi_hz(m), 0.16, [1, .35, .15],
                   attack=0.07, release=0.12, detune=0.003)
        bass = 36 + root                                        # basse : fondamentale puis quinte
        half = dur / 2
        _voice(buf, start, half, midi_hz(bass), 0.34, [1, .5, .2], attack=0.01, release=0.05, tau=0.35, sustain=0.5)
        if half > 0.05:
            _voice(buf, start + half, half, midi_hz(bass + (fifth - root) % 12), 0.28, [1, .5, .2],
                   attack=0.01, release=0.05, tau=0.35, sustain=0.5)
    # --- réverbération légère : peigne à contre-réaction (70 ms)
    d = int(0.070 * RATE)
    for i in range(d, len(buf)):
        buf[i] += 0.28 * buf[i - d]
    # niveau : même puissance moyenne (RMS) que l'onde carrée d'origine, pour que basculer d'un style à
    # l'autre ne change pas le volume ; la crête reste limitée à 0,9.
    active = [x for x in buf if abs(x) > 1e-4]
    rms = math.sqrt(sum(x * x for x in active) / max(1, len(active)))
    peak = max(1e-9, max(abs(x) for x in buf))
    gain = min(0.9 / peak, volume_to_amp(volume) / max(1e-9, rms))
    return array.array("h", (int(max(-1, min(1, x * gain)) * 32767) for x in buf))


def melody_audio(notes, volume=8, style="original"):
    return arrange_samples(notes, volume) if style == "arrange" else melody_samples(notes, volume)


class AYStream:
    """Les EFFETS SONORES du jeu : le code d'origine règle directement les registres de la puce AY (périodes des
    3 voix, mélangeur, volumes, bruit). Ici, à chaque image (20 ms) on lit ces registres et on fabrique les
    échantillons correspondants, avec une phase continue d'une image à l'autre."""
    BOOST = 3.0          # le volume d'origine (2 sur 15 par défaut) est très faible : on le renforce

    def __init__(self):
        self.phase = [0.0, 0.0, 0.0]
        self.noise_phase, self.lfsr, self.noise_bit = 0.0, 1, 1

    def chunk(self, regs, seconds=0.02):
        """Un tampon de 16 bits mono, ou None si rien n'est audible."""
        mixer = regs[7]
        voices = []
        for i in range(3):
            vol = regs[8 + i] & 15
            tone_on, noise_on = not (mixer >> i) & 1, not (mixer >> (3 + i)) & 1
            if vol and (tone_on or noise_on):
                period = ((regs[2 * i + 1] & 15) << 8) | regs[2 * i]
                voices.append((i, min(1.0, (vol / 15) * self.BOOST) * 0.25, AY_CLOCK / (16 * max(1, period)), tone_on, noise_on))
        if not voices:
            return None
        n = int(RATE * seconds)
        noise_step = AY_CLOCK / (16 * max(1, regs[6] & 31)) / RATE
        out = array.array("h", bytes(2 * n))
        phase = self.phase
        for k in range(n):
            self.noise_phase += noise_step
            while self.noise_phase >= 1.0:                 # registre à décalage de 17 bits du bruit
                self.noise_phase -= 1.0
                bit = (self.lfsr ^ (self.lfsr >> 3)) & 1
                self.lfsr = (self.lfsr >> 1) | (bit << 16)
                self.noise_bit = self.lfsr & 1
            acc = 0.0
            for i, amp, freq, tone_on, noise_on in voices:
                phase[i] = (phase[i] + freq / RATE) % 1.0
                level = (phase[i] < 0.5 if tone_on else True) and (self.noise_bit if noise_on else True)
                acc += amp if level else -amp
            out[k] = int(max(-1.0, min(1.0, acc)) * 32767)
        return out


def write_wav(path, samples):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(samples.tobytes())


# ---------------------------------------------------------------- lecture (pygame, optionnel)
class Sound:
    """Façade sonore. Si pygame ou la carte son manque : toutes les méthodes ne font rien, et `error`
    explique pourquoi.

    IMPORTANT : les sons sont envoyés à pygame sous forme de fichier WAV EN MÉMOIRE. pygame le convertit
    alors lui-même au format réel du mixeur (fréquence, mono/stéréo), quel que soit celui choisi par
    pygame.init(). (Envoyer des échantillons bruts supposait un mixeur 22 050 Hz mono : si le mixeur
    était déjà ouvert en 44 100 Hz stéréo, le son sortait ~4 fois trop vite.)"""
    def __init__(self, volume=8, style="original"):
        self.volume = volume                       # [$04FD] réglé dans le menu du jeu
        self.style = style                         # "original" (puce AY) ou "arrange" (instruments)
        self.ok = False
        self.error = None
        self.melodies = load_melodies()
        self._ay = AYStream()
        self._ay_channel = None
        self._samples = {}                         # échantillons calculés (calcul pur, sans pygame)
        self._cache = {}                           # objets pygame.mixer.Sound
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self._pg = pygame
            self.ok = True
        except Exception as e:                     # pygame absent ou pas de sortie audio
            self._pg = None
            self.error = f"{type(e).__name__}: {e}"

    # --- calcul en tâche de fond : évite un gel de la fenêtre au premier appui sur une touche
    def prepare(self):
        import threading
        def work():
            styles = [self.style] + [x for x in STYLES if x != self.style]
            for style in styles:
                for name, notes in self.melodies.items():
                    k = (("m", name), self.volume, style)
                    if k not in self._samples:
                        self._samples[k] = melody_audio(notes, self.volume, style)
            # les sons du saut et de la mort dépendent de la cadence du jeu : calculés à la demande
        threading.Thread(target=work, daemon=True).start()

    def _to_sound(self, samples):
        import io
        bio = io.BytesIO()
        write_wav(bio, samples)
        bio.seek(0)
        return self._pg.mixer.Sound(file=bio)

    def _play(self, key, make, styled=True):
        if not self.ok:
            return None
        k = (key, self.volume, self.style if styled else "-")
        snd = self._cache.get(k)
        if snd is None:
            samples = self._samples.get(k)
            if samples is None:                    # pas encore prêt : calcul immédiat
                samples = self._samples[k] = make(self.volume)
            snd = self._cache[k] = self._to_sound(samples)
        return snd.play()

    def play_melody(self, name):
        self.stop()
        self._play(("m", name), lambda v: melody_audio(self.melodies[name], v, self.style))

    def feed_ay(self, regs):
        """Appelée à chaque image : joue les effets décrits par les registres de la puce sonore du jeu."""
        if not self.ok:
            return
        chunk = self._ay.chunk(regs)
        if chunk is None:
            return
        if self._ay_channel is None:
            self._ay_channel = self._pg.mixer.Channel(7)
        ch = self._ay_channel
        snd = self._to_sound(chunk)
        if not ch.get_busy():
            ch.play(snd)
        elif ch.get_queue() is None:
            ch.queue(snd)

    def toggle_style(self):
        self.style = "arrange" if self.style == "original" else "original"
        return self.style

    def jump(self, tick_s=JUMP_TICK_S):
        """Démarre le son du saut ; il dure jusqu'à stop_jump() (appelé à l'atterrissage)."""
        self.stop_jump()
        key = ("jump", round(tick_s * 1000, 3))
        self._jump_channel = self._play(key, lambda v: jump_samples(v, tick_s), styled=False)

    def stop_jump(self):
        """[$1186] le son du saut est coupé dès que le héros n'est plus en l'air."""
        ch = getattr(self, "_jump_channel", None)
        if ch is not None:
            try:
                ch.fadeout(8)
            except Exception:
                ch.stop()
        self._jump_channel = None

    def death(self, segments=((24, 0.04),)):
        self.stop_jump()
        self._play(("death", tuple(segments)), lambda v: death_samples(v, segments), styled=False)

    def stop(self):
        if self.ok:
            self._pg.mixer.stop()


if __name__ == "__main__":
    # fichiers .wav pour écouter sans pygame
    for name, notes in load_melodies().items():
        write_wav(f"{name}_original.wav", melody_samples(notes, 8))
        write_wav(f"{name}_arrange.wav", arrange_samples(notes, 8))
        tonic, mode, plan = harmonize(notes)
        print(f"{name}: {len(notes)} notes, ~{sum(d for _, _, d in notes) * SEC_PER_UNIT:.1f} s, "
              f"tonalité {NOTE_NAMES[tonic]} {'majeur' if mode == 'maj' else 'mineur'}, "
              f"accords : " + " ".join(NOTE_NAMES[pcs[0]] for _, pcs in plan))
    write_wav("effet_saut.wav", jump_samples(8, 0.005, 20))          # saut de 41 tours de 5 ms
    write_wav("effet_mort.wav", death_samples(8, ((10, 0.015), (19, 0.030))))
