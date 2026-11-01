# DZ Subtitles AI - Remotion Engine & Pipeline Integration Guide

## 1. Overview & Tools Comparison

| Engine | Cost | Speed (30s Video) | Arabic RTL & BiDi | Recommended Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **FFmpeg + libass** *(Core Studio)* | **100% Free** | **~1.5 - 2.5s** | Native via FriBidi + HarfBuzz | Real-time web UI, instant rendering, batch queue processing |
| **Remotion (React)** *(Included here)* | **100% Free** (Indie) | **~15 - 30s** | Native WebKit Browser Engine (`dir="rtl"`, `<span dir="ltr">`) | n8n automated pipelines, custom React spring animations |
| **pycaps** *(Python CLI)* | 100% Free | ~25 - 45s | Playwright HTML | Simple Python scripts when Node.js is unavailable |
| **tscaps API** *(Cloud)* | Paid / Freemium | ~10 - 20s + Upload | Cloud CSS | Cloud servers without local GPU/CPU |

---

## 2. Running Remotion Locally

### Install dependencies:
```bash
cd remotion
npm install
```

### Live Preview in Browser:
```bash
npx remotion preview src/index.ts
```

### Render Video with Custom Props:
```bash
npx remotion render Captions out.mp4 --props=../output/<task_id>/remotion_props.json
```

---

## 3. n8n Automation Node Setup

In your n8n workflow:
1. **Whisper / Gemini Node**: Generates the word timestamps JSON.
2. **Execute Command Node**:
   ```bash
   npx remotion render Captions /output/reel_captions.mp4 --props='{{ JSON.stringify($json.remotion_props) }}'
   ```
3. **HTTP / Discord / YouTube Node**: Uploads the rendered short directly to social media!
