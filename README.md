# 🎙️ DZ Subtitles AI - مولّد الترجمة الجزائرية المتحركة

<div align="center">

![DZ Subtitles Banner](https://img.shields.io/badge/Language-Algerian_Darija_(الدارجة_الجزائرية)-brightgreen?style=for-the-badge)
![Gemini AI](https://img.shields.io/badge/AI_Engine-Google_Gemini_Free_API-blue?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)
![FFmpeg](https://img.shields.io/badge/Rendering-FFmpeg_+_libass-red?style=for-the-badge&logo=ffmpeg)
![License](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge)

**Automatic Animated Subtitle Generator for Algerian Arabic (Darija) with Gemini AI & Chroma Key Green Screen.**  
*توليد الترجمة المتحركة التلقائية للدارجة الجزائرية كلمة بكلمة مع كروما خضراء، شاشة سوداء، أو دمج مباشر على الفيديو.*

[⚡ Quick Start (ابدأ الآن)](#-quick-start) •
[✨ Features (المميزات)](#-features) •
[🎬 Video Editors Guide (دليل برامج المونتاج)](#-video-editors-guide-chroma-key) •
[⚙️ CLI Usage](#%EF%B8%8F-cli-usage) •
[🐳 Docker Setup](#-docker-setup) •
[🔄 n8n Workflow](#-n8n-workflow-integration)

</div>

---

## 🌟 Overview (نظرة عامة)

**DZ Subtitles AI** is an all-in-one AI tool designed to automatically transcribe spoken **Algerian Arabic (الدارجة الجزائرية)** from any audio or video file and generate **viral, animated, word-by-word subtitles** (in the style of TikTok, Instagram Reels, and YouTube Shorts).

It operates seamlessly:
- **Audio Inputs (.mp3, .wav, .m4a, etc.)**: Produces animated subtitles on a **Green Screen** (`#00FF00` Chroma Key), **Black Screen** (Screen Blend Mode), **Blue Screen**, or **Transparent Alpha Video (ProRes / WebM)** so your friends or editors can drop them right into Premiere Pro, DaVinci Resolve, or CapCut.
- **Video Inputs (.mp4, .mov, .mkv, etc.)**: Automatically burns the animated subtitles directly onto the original video with zero quality loss.
- **Subtitles Exporter**: Exports `.ass` (animated with colors and bounce), `.srt`, `.vtt`, and `.json` timestamps.

---

## ✨ Features (المميزات)

- 🇩🇿 **Trained for Algerian Darija**: Pre-tuned dialect prompts recognizing slang, loanwords, and accents across Algiers (العاصمة), Oran (الغرب), Constantine (الشرق), and general Algerian.
- ⚡ **Google Gemini Free API**: Fast, accurate transcription using free Gemini token access (`gemini-3.5-transcribe` / `gemini-flash-latest`) with automatic fallback cascade.
- 🔄 **Offline Fallback**: Includes local `faster-whisper` fallback if offline or API key is not supplied.
- 🎯 **Word-by-Word Animation**:
  - **Karaoke Pop & Scale** (Active word pops up and turns neon yellow/cyan as spoken).
  - **Progressive Reveal** (Words appear one by one with exact timing).
  - **Box Highlight & Badge** (Accent box behind the active word).
  - **Classic Subtitle Line** (Smooth fade in/out).
- 🔤 **Bundled Arabic Typography**: Comes bundled with Google OFL Arabic fonts: **Cairo**, **Tajawal**, **Almarai**, and **Amiri** (no need to install fonts manually on your system).
- 🖥️ **Ultra-Sleek Web Interface**: Responsive Dark Glassmorphism UI with real-time audio/video preview, interactive subtitle editor (allows editing any word or timestamp), and instant 1-click downloads.
- ⚙️ **Multi-Format Aspect Ratios**: 9:16 (Shorts/TikTok/Reels), 16:9 (YouTube/Landscape), 1:1 (Square).

---

## 🚀 Quick Start (ابدأ الآن في دقيقة واحدة)

### Option A: Windows (One-Click for your friend)
If you send this folder to your friend on Windows:
1. Double-click **`start.bat`**.
2. It will automatically check dependencies and open the web app at `http://localhost:8000` in their default browser!

### Option B: Linux / macOS
```bash
git clone https://github.com/Maliksouhildev/subtitles-generator-.git
cd subtitles-generator-
chmod +x start.sh
./start.sh
```

### Option C: Manual Setup (Python 3.10+)
```bash
# 1. Clone repository
git clone https://github.com/Maliksouhildev/subtitles-generator-.git
cd subtitles-generator-

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your free Gemini API Key (Optional if entered in the web UI)
# On Windows PowerShell:
$env:GEMINI_API_KEY="your_api_key_here"
# On Linux/macOS:
export GEMINI_API_KEY="your_api_key_here"

# 4. Run server
python server.py
```
Open **`http://localhost:8000`** in your browser.

---

## 🔑 How to Get a Free Gemini API Key (مجاني 100%)

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Sign in with any Google account.
3. Click **"Create API Key"**.
4. Copy the key and either:
   - Paste it in the `.env` file (`GEMINI_API_KEY=AIzaSy...`).
   - Or paste it directly in the **Gemini API Key** field in the Web Interface (it will be remembered in your browser).

---

## 🎬 Video Editors Guide (Chroma Key & Overlay)

### 1. CapCut (الهاتف أو الكمبيوتر)
1. قم برفع ملفك الصوتي في **DZ Subtitles AI** واختر خلفية **Green Screen** ومقاس **9:16**.
2. حمّل الفيديو الناتج (`result.mp4`).
3. في CapCut، افتح الفيديو الأساسي، ثم أضف فيديو الترجمة كـ **Overlay** (طبقة فوق الفيديو).
4. اضغط على طبقة الترجمة ثم اذهب إلى **Cutout / Remove BG** -> **Chroma Key**.
5. استخدم أداة القطّارة (Color Picker) لاختيار اللون الأخضر، واضبط الشدة (Intensity) بين 15% و 25%.
6. مبروك! الترجمة الآن متحركة بدقة فوق الفيديو الخاص بك.

### 2. Adobe Premiere Pro
1. ضع فيديو الكروما الخضراء في المسار `V2` فوق الفيديو الأصلي في `V1`.
2. من لوحة **Effects**، ابحث عن تأثير **Ultra Key** واسحبه فوق فيديو الترجمة.
3. في **Effect Controls**، اختر أداة القطارة لـ **Key Color** واضغط على اللون الأخضر. ستختفي الخلفية فوراً.

### 3. DaVinci Resolve
1. أضف فيديو الكروما في الـ Timeline فوق الفيديو.
2. اذهب إلى صفحة **Color** أو **Fusion**، واستخدم أداة **3D Keyer** أو **Delta Keyer** لسحب اللون الأخضر بنقرة واحدة.

### 4. وضع الشاشة السوداء (Black Screen - بدون كروما!)
إذا اخترت في الإعدادات **Black Screen**:
- في أي برنامج مونتاج، فقط غيّر نمط الدمج (**Blending Mode**) لطبقة الترجمة إلى **Screen** أو **Add**.
- ستختفي الخلفية السوداء ويبقى النص والأنيميشن ساطعاً بدون الحاجة لمفتاح كروما!

---

## ⚙️ CLI Usage (Command Line)

For power users, scripts, or automated batch pipelines:

```bash
# 1. Generate green screen subtitles from an MP3 file
python cli.py -i voice_note.mp3 -o output_green.mp4 --bg green_screen --font Cairo --style karaoke_pop

# 2. Burn subtitles directly onto an existing video
python cli.py -i input_clip.mp4 -o final_video.mp4 --bg original_video --highlight "#00F0FF"

# 3. Generate YouTube landscape format (16:9) with Black screen
python cli.py -i podcast.mp3 -o podcast_subtitles.mp4 --aspect-ratio 16:9 --bg black --font Tajawal

# 4. Use specific regional dialect (Oran / West)
python cli.py -i speech.mp3 -o result.mp4 --dialect "Oran (West)"
```

### CLI Arguments:
| Argument | Description | Default |
|---|---|---|
| `-i, --input` | Path to audio or video file | Required |
| `-o, --output` | Output video filename | `output.mp4` |
| `--bg` | Background mode (`green_screen`, `black`, `blue`, `original_video`, `transparent`, `custom`) | `green_screen` |
| `--font` | Font name (`Cairo`, `Tajawal`, `Almarai`, `Amiri`) | `Cairo` |
| `--font-size` | Font size in pixels | `56` |
| `--highlight-color` | Spoken word highlight hex color | `#FFE600` |
| `--primary-color` | Inactive text hex color | `#FFFFFF` |
| `--style` | Animation (`karaoke_pop`, `word_reveal`, `box_highlight`, `classic_line`) | `karaoke_pop` |
| `--words-per-line` | Words per line chunk | `3` |
| `--aspect-ratio` | Video ratio (`9:16`, `16:9`, `1:1`) | `9:16` |
| `--dialect` | Algerian dialect focus | `General Algerian` |
| `--api-key` | Google Gemini API Key | Environment |

---

## 🐳 Docker Setup

Run the entire application in a Docker container with zero local dependency management:

```bash
# Using Docker Compose
docker compose up --build
```
Access the app at `http://localhost:8000`.

---

## 🔄 n8n Workflow Integration

If you use **n8n**, a ready-to-import workflow is included in:
📁 `workflows/darija_subtitles_n8n_workflow.json`

### To use in n8n:
1. Open your n8n workspace.
2. Click **Import from File** and select `workflows/darija_subtitles_n8n_workflow.json`.
3. Set your `GEMINI_API_KEY` credential in n8n.
4. Send an audio file via `POST /webhook/darija-subtitles` to automatically receive full Darija word timestamps and the animated `.ass` track!

---

## ⚛️ Remotion React Integration

For React and motion graphics developers, a Remotion composition template is included in:
📁 `remotion/SubtitlesComposition.tsx`

It demonstrates how to consume the generated `transcript.json` word timestamps and animate them using React spring physics:
```bash
cd remotion
npm install
npm start
```

---

## 🧪 Testing & Verification

Run the comprehensive automated test suite:
```bash
python -m pytest tests/ -v
```
All 17 tests verify:
- Right-to-Left Arabic text formatting and BGR hex conversions.
- Word-level timecode interpolation and JSON cleaning.
- Synthetic FFmpeg audio duration detection and video rendering.
- Green screen creation, video subtitle burning, and REST API endpoints.

---

## 📄 License

MIT License. Free to use, modify, and distribute for personal and commercial projects.
Built with ❤️ for Algerian content creators and the Algerian developer community.
