import os
import json
import asyncio
import requests
import subprocess
import glob
import random
import edge_tts
from google import genai
from google.genai import types
from mutagen.mp3 import MP3

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
GEMINI_MODEL_NAME = "gemini-2.5-flash"
BATCH_SIZE = 5

PROMPT_FILEPATH = 'prompt.txt'
PENDING_TOPICS_FILEPATH = 'pending_topics.txt'
PROCESSED_TOPICS_FILEPATH = 'processed_topics.txt'
MUSIC_DIR = "background_music"  
FINAL_OUTPUT_DIR = "final_videos"

MUSIC_TRACKS = {
    "track-2.mp3": "0.3"
}

client = genai.Client(api_key=GEMINI_API_KEY)

def clean_filename(text):
    return text.strip().replace(" ", "_").replace("(", "").replace(")", "")

def generate_script(topic, project_dir):
    print(f"--- Step 1: Generating script for {topic} ---")
    
    script_path = os.path.join(project_dir, "script.json")
    
    if os.path.exists(script_path):
        print("Script already exists, skipping generation")
        return script_path

    with open(PROMPT_FILEPATH, 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    final_prompt = prompt_template.format(topic=topic)

    response = client.models.generate_content(
        model=GEMINI_MODEL_NAME,
        contents=final_prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=65536,
            response_mime_type="application/json"
        )
    )

    with open(script_path, "w", encoding="utf-8") as f:
        f.write(response.text)
    
    return script_path

async def generate_audio_segment(text, filename):
    communicate = edge_tts.Communicate(
        text,
        "es-MX-JorgeNeural",
        rate="-1%",
        volume="+0%",
        pitch="-30Hz"
    )
    await communicate.save(filename)

def process_audio(script_path, audio_dir):
    print(f"--- Step 2: Generating audio ---")
    
    with open(script_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    tasks = []
    
    for i, segment in enumerate(data["segmentos"]):
        clean_name = clean_filename(segment["nombre"])
        output_filename = os.path.join(audio_dir, f"{i:02d}_{clean_name}.mp3")
        
        print(f"Generating audio: {segment['nombre']}")
        asyncio.run(generate_audio_segment(segment["texto"], output_filename))

def download_assets(script_path, audio_dir, video_dir):
    print(f"--- Step 3: Downloading video assets ---")
    
    headers = {"Authorization": PEXELS_API_KEY}
    
    with open(script_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    used_video_ids = set()

    for i, segment in enumerate(data["segmentos"]):
        clean_name = clean_filename(segment["nombre"])
        video_filename = os.path.join(video_dir, f"{i:02d}_{clean_name}.mp4")
        audio_filename = os.path.join(audio_dir, f"{i:02d}_{clean_name}.mp3")
        
        if not os.path.exists(audio_filename):
            print(f"Warning: Audio missing for segment {i}, skipping video")
            continue

        audio = MP3(audio_filename)
        audio_duration = audio.info.length
        
        search_term = segment["descripcion_visual"]
        query = f"{search_term}, dark, cinematic"
        
        page_num = random.randint(1, 3) 
        print(f"Searching: {query} (Min duration: {audio_duration:.2f}s, Page: {page_num})")
        
        try:
            response = requests.get(
                "https://api.pexels.com/videos/search", 
                headers=headers, 
                params={
                    "query": query, 
                    "orientation": "portrait", 
                    "per_page": 15,
                    "page": page_num
                }
            )

            if response.status_code == 200:
                result = response.json()
                valid_candidates = []
                
                for video in result.get("videos", []):
                    if video["duration"] >= audio_duration and video["id"] not in used_video_ids:
                        valid_candidates.append(video)
                
                selected_video = None

                if valid_candidates:
                    selected_video = random.choice(valid_candidates)
                    used_video_ids.add(selected_video["id"])
                
                elif result.get("videos"):
                     print("No strict match found, using fallback from results.")
                     selected_video = result["videos"][0]

                if selected_video:
                    video_files = selected_video["video_files"]
                    best_video = next((v for v in video_files if v["width"] >= 1080), video_files[0])
                    
                    print(f"Downloading to {video_filename}")
                    content = requests.get(best_video["link"]).content
                    with open(video_filename, 'wb') as f:
                        f.write(content)
                else:
                    print(f"No suitable video found for segment {i}")
            else:
                print(f"Pexels API Error: {response.status_code}")
                
        except Exception as e:
            print(f"Exception during download: {e}")

def assemble_video(project_dir, audio_dir, video_dir):
    print(f"--- Step 4: Assembling base video ---")
    
    temp_ts_dir = os.path.join(project_dir, "ts_segments")
    if not os.path.exists(temp_ts_dir):
        os.makedirs(temp_ts_dir)
        
    concat_list_path = os.path.join(project_dir, "concat_list.txt")
    output_base_video = os.path.join(project_dir, "base_video.mp4")
    
    audio_files = sorted(glob.glob(os.path.join(audio_dir, "*.mp3")))
    video_files = sorted(glob.glob(os.path.join(video_dir, "*.mp4")))
    
    if not audio_files or not video_files:
        print(f"Error: Missing audio or video files in {project_dir}")
        return None

    with open(concat_list_path, 'w', encoding='utf-8') as list_file:
        for audio_path, video_path in zip(audio_files, video_files):
            filename = os.path.basename(audio_path)
            segment_index = filename.split('_')[0]
            temp_ts_path = os.path.join(temp_ts_dir, f"segment_{segment_index}.ts")
            
            abs_ts_path = os.path.abspath(temp_ts_path)

            cmd = [
                "ffmpeg", "-y",
                "-stream_loop", "-1",
                "-i", video_path,
                "-i", audio_path,
                "-map", "0:v:0", "-map", "1:a:0",
                "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                "-c:v", "libx264", "-c:a", "aac",
                "-f", "mpegts", "-shortest",
                temp_ts_path
            ]
            
            subprocess.run(cmd, check=True)
            list_file.write(f"file '{abs_ts_path}'\n")
            
    print("Concatenating segments...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_path, "-c", "copy",
        "-bsf:a", "aac_adtstoasc", output_base_video
    ], check=True) 
    
    return output_base_video

def add_music(base_video, final_output_path):
    print(f"--- Step 5: Mixing music ---")
    
    available_tracks = list(MUSIC_TRACKS.keys())
    
    if not available_tracks:
        print("Error: No tracks defined in MUSIC_TRACKS config.")
        return

    selected_track_name = random.choice(available_tracks)
    
    selected_volume = MUSIC_TRACKS[selected_track_name]
    
    music_path = os.path.join(MUSIC_DIR, selected_track_name)
    
    if not os.path.exists(music_path):
        print(f"Error: Music file '{selected_track_name}' not found in {MUSIC_DIR}")
        return

    print(f"Selected Track: {selected_track_name}")
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", "10", 
        "-stream_loop", "-1", "-i", music_path,
        "-i", base_video,
        "-filter_complex", f"[0:a]volume={selected_volume}[music];[1:a]volume=1.0[voice];[music][voice]amix=inputs=2:duration=shortest[audio_out]",
        "-map", "1:v:0",
        "-map", "[audio_out]",
        "-c:v", "copy", "-c:a", "aac",
        "-shortest",
        final_output_path
    ]
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    print(f"Final video saved: {final_output_path}")

def main():
    if not os.path.exists(FINAL_OUTPUT_DIR):
        os.makedirs(FINAL_OUTPUT_DIR)
        
    with open(PENDING_TOPICS_FILEPATH, 'r', encoding='utf-8') as f:
        all_topics = f.read().splitlines()
        
    topics_to_process = all_topics[:BATCH_SIZE]
    remaining_topics = all_topics[BATCH_SIZE:]
    
    successfully_processed_topics = []
    
    for topic in topics_to_process:
        if not topic.strip(): continue
        
        safe_name = clean_filename(topic)
        print(f"\n==========================================")
        print(f"PROCESSING TOPIC: {topic}")
        print(f"==========================================\n")
        
        project_dir = os.path.join("temp_work", safe_name)
        audio_dir = os.path.join(project_dir, "audio")
        video_dir = os.path.join(project_dir, "video")
        
        for d in [audio_dir, video_dir]:
            if not os.path.exists(d):
                os.makedirs(d)

        try:
            script_path = generate_script(topic, project_dir)
            process_audio(script_path, audio_dir)
            download_assets(script_path, audio_dir, video_dir)
            base_video = assemble_video(project_dir, audio_dir, video_dir)
            
            final_output = os.path.join(FINAL_OUTPUT_DIR, f"{safe_name}.mp4")
            add_music(base_video, final_output)
            
            successfully_processed_topics.append(topic)
            
        except Exception as e:
            print(f"Error processing {topic}: {str(e)}")
            
    with open(PENDING_TOPICS_FILEPATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(remaining_topics) + '\n')
        
    with open(PROCESSED_TOPICS_FILEPATH, 'a', encoding='utf-8') as f:
            f.write('\n'.join(successfully_processed_topics) + '\n')
            
    print(f"\n--- Batch Complete ---")
    print(f"Processed: {len(successfully_processed_topics)}")
    print(f"Remaining in queue: {len(remaining_topics)}")

if __name__ == "__main__":
    main()