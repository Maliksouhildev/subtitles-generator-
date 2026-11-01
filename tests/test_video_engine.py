import os
import subprocess
import pytest
from core.ass_builder import ASSSubtitleBuilder
from core.video_engine import render_video, is_video_file, get_audio_duration


@pytest.fixture(scope="module")
def sample_media():
    os.makedirs("sample_data", exist_ok=True)
    audio_file = os.path.join("sample_data", "test_tone.mp3")
    video_file = os.path.join("sample_data", "test_clip.mp4")

    # Generate 2-second audio if not existing
    if not os.path.exists(audio_file):
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-c:a", "mp3",
            audio_file
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Generate 2-second video if not existing
    if not os.path.exists(video_file):
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=blue:s=640x360:d=2:r=25",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac",
            video_file
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return audio_file, video_file


def test_audio_duration_and_type(sample_media):
    audio_file, video_file = sample_media
    dur = get_audio_duration(audio_file)
    assert dur >= 1.9

    assert not is_video_file(audio_file)
    assert is_video_file(video_file)


def test_render_audio_green_screen(sample_media, tmp_path):
    audio_file, _ = sample_media

    # Generate ASS
    builder = ASSSubtitleBuilder(
        font_name="Cairo",
        font_size=40,
        primary_color="#FFFFFF",
        highlight_color="#00FFFF",
        animation_style="karaoke_pop"
    )
    ass_content = builder.generate_ass({
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.0,
                "text": "سلام عليكم الجزائر",
                "words": [
                    {"word": "سلام", "start": 0.0, "end": 0.5},
                    {"word": "عليكم", "start": 0.5, "end": 1.0},
                    {"word": "الجزائر", "start": 1.0, "end": 2.0}
                ]
            }
        ]
    })

    ass_path = str(tmp_path / "test.ass")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    out_mp4 = str(tmp_path / "green_screen.mp4")
    rendered = render_video(
        media_path=audio_file,
        ass_path=ass_path,
        output_path=out_mp4,
        background_mode="green_screen",
        aspect_ratio="9:16"
    )

    assert os.path.exists(rendered)
    assert os.path.getsize(rendered) > 1000
    assert is_video_file(rendered)


def test_render_video_burn_subtitles(sample_media, tmp_path):
    _, video_file = sample_media

    builder = ASSSubtitleBuilder(
        font_name="Tajawal",
        font_size=32,
        primary_color="#FFFFFF",
        highlight_color="#FFE600",
        animation_style="karaoke_pop"
    )
    ass_content = builder.generate_ass({
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.0,
                "text": "واش راكم خاوتي",
                "words": [
                    {"word": "واش", "start": 0.0, "end": 0.6},
                    {"word": "راكم", "start": 0.6, "end": 1.2},
                    {"word": "خاوتي", "start": 1.2, "end": 2.0}
                ]
            }
        ]
    })

    ass_path = str(tmp_path / "test_burn.ass")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    out_mp4 = str(tmp_path / "burned_video.mp4")
    rendered = render_video(
        media_path=video_file,
        ass_path=ass_path,
        output_path=out_mp4,
        background_mode="original_video"
    )

    assert os.path.exists(rendered)
    assert os.path.getsize(rendered) > 1000
    assert is_video_file(rendered)
