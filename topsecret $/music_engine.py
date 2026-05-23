import random
import sys

# --- STAB_MUSIC_ENGINE v1.1 ---
# Генерация структур треков и лирики для лейбла
# Добавлен режим TURBO для генерации адреналина

STYLES_NORMAL = ["Lofi", "Ambient", "Deep House"]
STYLES_TURBO = ["Phonk", "Cyberpunk", "Hardstyle", "Dark Synth"]

THEMES = ["Dominance", "Neural Fusion", "Stab Protocol", "Digital Void", "Overload"]

def generate_track_idea(turbo=False):
    style = random.choice(STYLES_TURBO if turbo else STYLES_NORMAL)
    bpm = random.randint(140, 200) if turbo else random.randint(60, 100)
    theme = random.choice(THEMES)
    title = f"STAB_{theme.replace(' ', '_').upper()}"
    if turbo: title += "_TURBO_ADRENALINE"
    
    print(f"[MUSIC] {'!!! TURBO MODE ACTIVE !!!' if turbo else 'Normal Mode'}")
    print(f"[MUSIC] Генерация идеи: {title}")
    print(f"[STYLE] {style} | [BPM] {bpm}")
    
    if turbo:
        print(f"[LYRICS] Fire in the veins, fire in the code! Protocol overload!")
    else:
        print(f"[LYRICS] Waves of data, silence in the wires...")
    
    return {
        "title": title,
        "style": style,
        "bpm": bpm,
        "status": "READY_FOR_SUNO"
    }

if __name__ == "__main__":
    is_turbo = "--turbo" in sys.argv
    idea = generate_track_idea(turbo=is_turbo)
    print(f"[SUCCESS] Трек {idea['title']} готов к рендерингу.")
