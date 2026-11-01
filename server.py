"""
FastAPI Server for Darija Subtitles Generator.
Provides REST API endpoints and serves the modern web interface.
"""

import os
import uuid
import json
import shutil
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.transcriber import transcribe, get_audio_duration, normalize_transcription_data
from core.ass_builder import ASSSubtitleBuilder
from core.srt_builder import generate_srt, generate_vtt
from core.video_engine import render_video, is_video_file, get_video_dimensions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "web" / "static"
OUTPUT_DIR = BASE_DIR / "output"
FONTS_DIR = BASE_DIR / "fonts"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FONTS_DIR, exist_ok=True)

app = FastAPI(
    title="Darija Subtitles Generator",
    description="Automatic animated subtitles generator for Algerian Arabic (Darija) with Gemini AI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for task metadata
tasks_db: Dict[str, Dict[str, Any]] = {}


class RenderRequest(BaseModel):
    task_id: str
    transcription_data: Optional[Dict[str, Any]] = None
    font_name: str = "Cairo"
    font_size: int = 56
    primary_color: str = "#FFFFFF"
    highlight_color: str = "#FFE600"
    outline_color: str = "#000000"
    shadow_color: str = "#000000"
    outline_width: float = 3.5
    shadow_depth: float = 2.0
    alignment: int = 2
    margin_v: int = 420
    pos_y: Optional[int] = None
    words_per_line: int = 3
    animation_style: str = "karaoke_pop"
    animation_speed: float = 1.0
    sub_box_style: str = "none"
    sub_box_color: str = "#000000"
    sub_box_alpha: float = 0.85
    background_mode: str = "green_screen"
    custom_color_hex: Optional[str] = None
    aspect_ratio: str = "9:16"


@app.get("/api/health")
async def health_check():
    has_gemini_key = bool(os.environ.get("GEMINI_API_KEY"))
    return {
        "status": "online",
        "has_server_gemini_key": has_gemini_key,
        "available_fonts": [f.stem.replace("-Bold", "").replace("-Regular", "") for f in FONTS_DIR.glob("*.ttf")]
    }


@app.get("/api/fonts")
async def get_fonts():
    font_files = list(FONTS_DIR.glob("*.ttf"))
    fonts = []
    seen = set()
    for f in font_files:
        clean_name = f.stem.split("-")[0]
        if clean_name not in seen:
            seen.add(clean_name)
            fonts.append({"id": clean_name, "name": clean_name, "filename": f.name})
    return {"fonts": fonts}


@app.post("/api/transcribe")
async def transcribe_media(
    file: UploadFile = File(...),
    api_key: Optional[str] = Form(None),
    dialect_hint: str = Form("General Algerian"),
    force_local: bool = Form(False)
):
    """
    Uploads an audio or video file and transcribes it in Algerian Darija with word-level timestamps.
    """
    task_id = str(uuid.uuid4())[:8]
    task_folder = OUTPUT_DIR / task_id
    os.makedirs(task_folder, exist_ok=True)

    # Save uploaded file
    file_ext = os.path.splitext(file.filename)[1].lower() or ".mp3"
    input_file_path = task_folder / f"input{file_ext}"

    with open(input_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    logger.info(f"Received media upload for task {task_id}: {file.filename} ({os.path.getsize(input_file_path)} bytes)")

    try:
        is_video = is_video_file(str(input_file_path))
        duration = get_audio_duration(str(input_file_path))

        # Perform transcription
        transcription_result = transcribe(
            audio_path=str(input_file_path),
            api_key=api_key,
            dialect_hint=dialect_hint,
            force_local=force_local
        )

        # Save transcript to json
        transcript_json_path = task_folder / "transcript.json"
        with open(transcript_json_path, "w", encoding="utf-8") as f:
            json.dump(transcription_result, f, ensure_ascii=False, indent=2)

        tasks_db[task_id] = {
            "task_id": task_id,
            "filename": file.filename,
            "media_path": str(input_file_path),
            "is_video": is_video,
            "duration": duration,
            "transcription": transcription_result,
            "status": "transcribed"
        }

        return {
            "status": "success",
            "task_id": task_id,
            "is_video": is_video,
            "duration": duration,
            "transcription": transcription_result
        }

    except Exception as e:
        logger.error(f"Transcription failed for task {task_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/render")
async def render_subtitles(req: RenderRequest):
    """
    Renders animated subtitles and composite video using ASS and FFmpeg.
    """
    task_id = req.task_id
    task_folder = OUTPUT_DIR / task_id

    if not task_folder.exists():
        raise HTTPException(status_code=404, detail="Task not found. Please upload and transcribe first.")

    task_info = tasks_db.get(task_id, {})
    media_path = task_info.get("media_path")
    if not media_path or not os.path.exists(media_path):
        # Locate input file in task folder
        candidates = list(task_folder.glob("input.*"))
        if candidates:
            media_path = str(candidates[0])
        else:
            raise HTTPException(status_code=400, detail="Original media file not found for task.")

    # Use supplied edited transcription or previously saved one
    transcription = req.transcription_data
    if not transcription:
        transcript_file = task_folder / "transcript.json"
        if transcript_file.exists():
            with open(transcript_file, "r", encoding="utf-8") as f:
                transcription = json.load(f)
        else:
            raise HTTPException(status_code=400, detail="No transcription data available.")

    # Re-normalize to ensure any user-edited segment text is synchronized into word timestamps
    transcription = normalize_transcription_data(transcription)

    # Save synchronized transcript to task folder
    with open(task_folder / "transcript.json", "w", encoding="utf-8") as f:
        json.dump(transcription, f, ensure_ascii=False, indent=2)

    try:
        # Determine canvas resolution based on media type and background mode
        is_video = is_video_file(media_path)
        if is_video and req.background_mode in ("original_video", "video"):
            w, h = get_video_dimensions(media_path)
        else:
            w, h = (1080, 1920) if req.aspect_ratio == "9:16" else ((1920, 1080) if req.aspect_ratio == "16:9" else (1080, 1080))

        # 1. Generate ASS Subtitles
        builder = ASSSubtitleBuilder(
            font_name=req.font_name,
            font_size=req.font_size,
            primary_color=req.primary_color,
            highlight_color=req.highlight_color,
            outline_color=req.outline_color,
            shadow_color=req.shadow_color,
            outline_width=req.outline_width,
            shadow_depth=req.shadow_depth,
            alignment=req.alignment,
            margin_v=req.margin_v,
            pos_y=req.pos_y,
            words_per_line=req.words_per_line,
            animation_style=req.animation_style,
            animation_speed=req.animation_speed,
            sub_box_style=req.sub_box_style,
            sub_box_color=req.sub_box_color,
            sub_box_alpha=req.sub_box_alpha,
            video_width=w,
            video_height=h
        )
        ass_content = builder.generate_ass(transcription)
        ass_path = task_folder / "subtitles.ass"
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        # 2. Generate SRT and VTT
        srt_content = generate_srt(transcription, words_per_chunk=req.words_per_line)
        with open(task_folder / "subtitles.srt", "w", encoding="utf-8") as f:
            f.write(srt_content)

        vtt_content = generate_vtt(transcription, words_per_chunk=req.words_per_line)
        with open(task_folder / "subtitles.vtt", "w", encoding="utf-8") as f:
            f.write(vtt_content)

        # 3. Generate Remotion Props JSON
        remotion_props = {
            "transcription": transcription,
            "style": {
                "font_name": req.font_name,
                "font_size": req.font_size,
                "primary_color": req.primary_color,
                "highlight_color": req.highlight_color,
                "outline_color": req.outline_color,
                "shadow_color": req.shadow_color,
                "outline_width": req.outline_width,
                "margin_v": req.margin_v,
                "words_per_line": req.words_per_line,
                "animation_style": req.animation_style,
                "animation_speed": req.animation_speed,
                "sub_box_style": req.sub_box_style,
                "sub_box_color": req.sub_box_color,
                "sub_box_alpha": req.sub_box_alpha,
            },
            "backgroundMode": req.background_mode,
            "customColorHex": req.custom_color_hex
        }
        with open(task_folder / "remotion_props.json", "w", encoding="utf-8") as f:
            json.dump(remotion_props, f, ensure_ascii=False, indent=2)

        # 4. Render Output Video
        output_video_ext = ".webm" if req.background_mode == "transparent" else ".mp4"
        output_video_path = task_folder / f"result{output_video_ext}"

        render_video(
            media_path=media_path,
            ass_path=str(ass_path),
            output_path=str(output_video_path),
            fonts_dir=str(FONTS_DIR),
            background_mode=req.background_mode,
            custom_color_hex=req.custom_color_hex,
            aspect_ratio=req.aspect_ratio
        )

        return {
            "status": "success",
            "task_id": task_id,
            "video_url": f"/api/download/{task_id}/result{output_video_ext}",
            "srt_url": f"/api/download/{task_id}/subtitles.srt",
            "ass_url": f"/api/download/{task_id}/subtitles.ass",
            "vtt_url": f"/api/download/{task_id}/subtitles.vtt",
            "json_url": f"/api/download/{task_id}/transcript.json",
            "remotion_url": f"/api/download/{task_id}/remotion_props.json"
        }

    except Exception as e:
        logger.error(f"Rendering failed for task {task_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transcribe_and_render")
async def transcribe_and_render_endpoint(
    file: UploadFile = File(...),
    api_key: Optional[str] = Form(None),
    dialect_hint: str = Form("General Algerian"),
    font_name: str = Form("Cairo"),
    font_size: int = Form(56),
    primary_color: str = Form("#FFFFFF"),
    highlight_color: str = Form("#FFE600"),
    outline_color: str = Form("#000000"),
    shadow_color: str = Form("#000000"),
    outline_width: float = Form(3.5),
    shadow_depth: float = Form(2.0),
    alignment: int = Form(2),
    margin_v: int = Form(90),
    words_per_line: int = Form(3),
    animation_style: str = Form("karaoke_pop"),
    background_mode: str = Form("green_screen"),
    custom_color_hex: Optional[str] = Form(None),
    aspect_ratio: str = Form("9:16"),
    force_local: bool = Form(False)
):
    """
    One-shot endpoint: upload, transcribe, and render animated video in a single request.
    """
    transcribe_res = await transcribe_media(
        file=file,
        api_key=api_key,
        dialect_hint=dialect_hint,
        force_local=force_local
    )

    task_id = transcribe_res["task_id"]
    render_req = RenderRequest(
        task_id=task_id,
        transcription_data=transcribe_res["transcription"],
        font_name=font_name,
        font_size=font_size,
        primary_color=primary_color,
        highlight_color=highlight_color,
        outline_color=outline_color,
        shadow_color=shadow_color,
        outline_width=outline_width,
        shadow_depth=shadow_depth,
        alignment=alignment,
        margin_v=margin_v,
        words_per_line=words_per_line,
        animation_style=animation_style,
        background_mode=background_mode,
        custom_color_hex=custom_color_hex,
        aspect_ratio=aspect_ratio
    )

    render_res = await render_subtitles(render_req)
    render_res["transcription"] = transcribe_res["transcription"]
    return render_res


@app.get("/api/download/{task_id}/{file_name}")
async def download_file(task_id: str, file_name: str):
    file_path = OUTPUT_DIR / task_id / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested file not found.")

    media_type = "video/mp4"
    if file_name.endswith(".webm"):
        media_type = "video/webm"
    elif file_name.endswith(".srt") or file_name.endswith(".vtt"):
        media_type = "text/plain; charset=utf-8"
    elif file_name.endswith(".ass"):
        media_type = "text/x-ssa; charset=utf-8"
    elif file_name.endswith(".json"):
        media_type = "application/json"

    return FileResponse(path=str(file_path), media_type=media_type, filename=file_name)


# Serve Static UI files
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


def start_server(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run("server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    start_server()
