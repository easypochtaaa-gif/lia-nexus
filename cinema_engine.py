import os
from moviepy.editor import VideoFileClip, AudioFileClip

# --- CONFIGURATION ---
INPUT_DIR = "raw_clips"
OUTPUT_DIR = "final_edits"
MUSIC_FILE = "stab_anthem.mp3"

def assemble_tiktok_video(clip_name):
    print(f"[*] Processing {clip_name}...")
    try:
        # 1. Load Video
        video = VideoFileClip(os.path.join(INPUT_DIR, clip_name))
        
        # 2. Try Load Audio
        if os.path.exists(MUSIC_FILE) and os.path.getsize(MUSIC_FILE) > 1024:
            try:
                audio = AudioFileClip(MUSIC_FILE).subclip(0, video.duration)
                video = video.set_audio(audio)
                print("[+] Audio synced.")
            except:
                print("[!] Audio failed, proceeding with silent video.")
        else:
            print("[!] No valid audio found, creating silent clip.")

        # 3. Final Export
        output_path = os.path.join(OUTPUT_DIR, f"FINAL_{clip_name}")
        video.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac")
        print(f"[+ SUCCESSFULLY COMPLETED]: {output_path}")
    except Exception as e:
        print(f"[ERROR]: {str(e)}")

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    if not os.path.exists(INPUT_DIR): os.makedirs(INPUT_DIR)
    
    print("--- STAB_CINEMA_ENGINE v1.1 (Resilient Mode) ---")
    clips = [f for f in os.listdir(INPUT_DIR) if f.endswith(('.mp4', '.mov'))]
    
    if not clips:
        print("[!] No clips found in 'raw_clips' folder.")
    else:
        for clip in clips:
            assemble_tiktok_video(clip)
