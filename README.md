# 🎬 TikTok video generator

An automated end-to-end system designed for the mass creation of vertical video content (TikTok/Reels/Shorts format). This project integrates Generative Artificial Intelligence, speech synthesis, and multimedia processing to transform simple text ideas into complete audiovisual productions without human intervention.

## 🚀 Main features

* **Intelligent scripting (GenAI):** Integration with **Google Gemini 2.5 Flash** to generate structured scripts, optimized for audience retention.
* **Realistic narration (TTS):** Implementation of **Edge TTS** to generate natural and emotive voiceovers in neutral Spanish.
* **Dynamic resource selection:** Automatic search and download of stock footage (Pexels API) based on the semantic analysis of the script.
* **Automated editing (FFmpeg):** Video rendering using `subprocess`, including cutting, resizing to 9:16, audio/video synchronization, and background music mixing (automatic ducking).
* **Batch processing:** Robust queue system capable of processing multiple topics sequentially, managing states (pending vs. processed).
* **Asynchronous architecture:** Use of `asyncio` to optimize blocking I/O operations such as audio generation.

## 🛠️ Technology stack

This project demonstrates competencies in the following technologies and libraries:

* **Language:** Python 3
* **External APIs:** Google GenAI SDK, Pexels API.
* **Multimedia:** FFmpeg (advanced A/V manipulation), Mutagen (audio metadata analysis).
* **Concurrency:** AsyncIO (asynchronous programming).
* **File management:** JSON, OS, Glob.

## ⚙️ Workflow architecture

The script follows a linear pipeline pattern with exception handling:

1. **Ingestion:** Reads a topic from `pending_topics.txt`.
2. **Content generation:**

* Queries the Gemini API to get a JSON script with time segments and visual descriptions.

3. **Audio synthesis:** Converts the text of each segment into individual `.mp3` files.
4. **Media acquisition:**

* Iterates over each audio segment.
* Searches Pexels for vertical videos matching the "visual description" suggested by the AI.
* Filters results by duration and quality (minimum 1080p).

5. **Assembly (rendering):**

* Concatenates Audio+Video pairs using FFmpeg.
* Applies crop filters to ensure the 9:16 aspect ratio.

6. **Post-production:**

* Adds a random music track from the local library.
* Adjusts volume levels (voice and background mix).

7. **Finalization:** Moves the rendered video to the output folder and updates the records of processed topics.

## 📋 Prerequisites

To run this project locally, you need:

1. **Python 3.8+** installed.
2. **FFmpeg** installed and added to the system PATH.
3. Environment variables configured:

* `GEMINI_API_KEY`: Your Google AI Studio API key.
* `PEXELS_API_KEY`: Your Pexels API key.

### Dependency installation

```bash
pip install google-genai edge-tts requests mutagen
```

## 📂 Project structure

```text
├── background_music/      # Library of .mp3 audio tracks
├── final_videos/          # Output of rendered videos
├── prompt.txt             # AI prompt engineering template
├── pending_topics.txt     # Input list (topics to generate)
├── processed_topics.txt   # Record of completed jobs
├── main.py                # Main orchestration script
└── README.md              # Documentation
```

## 💡 Overcome challenges and learnings

During the development of this tool, key technical challenges were resolved:

* **A/V synchronization:** Logic was implemented to ensure the video clip duration matches or exceeds the narrative audio duration before concatenation.
* **API error handling:** Implementation of "fallback" mechanisms when the Pexels API does not find exact matches for complex terms.
* **FFmpeg optimization:** Construction of complex filtering commands (`filter_complex`) to mix audio and video in a single render pass, reducing processing time.

## 🔮 Future improvements

* Implementation of automatic subtitles (burn-in subtitles) synchronized with the audio.
* Integration with the YouTube Data API for automatic uploading of generated videos.
* Dockerization of the environment to facilitate cloud deployment.
