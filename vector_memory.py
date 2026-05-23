import os, json, time
from pathlib import Path

# Simple vector placeholder: convert JSON values to a list of floats
def json_to_vector(data):
    # flatten numeric values (ints/floats) into a list
    vec = []
    def recurse(v):
        if isinstance(v, (int, float)):
            vec.append(float(v))
        elif isinstance(v, dict):
            for val in v.values():
                recurse(val)
        elif isinstance(v, list):
            for item in v:
                recurse(item)
    recurse(data)
    # pad / truncate to 256 dimensions
    if len(vec) < 256:
        vec.extend([0.0] * (256 - len(vec)))
    return vec[:256]

def save_vector(vec, out_path):
    import numpy as np
    arr = np.array(vec, dtype='float32')
    arr.tofile(out_path)

def watch_folder(folder_path):
    folder = Path(folder_path)
    memory_path = folder / 'memory.json'
    faiss_path = folder / 'memory_vectors' / 'faiss_index.bin'
    os.makedirs(faiss_path.parent, exist_ok=True)
    print(f"[VECTOR] Watching {folder} for changes…")
    last_mtime = None
    while True:
        if memory_path.exists():
            mtime = memory_path.stat().st_mtime
            if last_mtime is None or mtime != last_mtime:
                last_mtime = mtime
                with open(memory_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                vec = json_to_vector(data)
                save_vector(vec, faiss_path)
                print(f"[VECTOR] Updated vector ({len(vec)} dims) -> {faiss_path.name}")
        time.sleep(2)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Watch sync folder and build vector memory')
    parser.add_argument('--watch', required=True, help='Path to the sync folder')
    args = parser.parse_args()
    watch_folder(args.watch)
