import os
import shutil
import pytest
from fastapi.testclient import TestClient
from server import app, OUTPUT_DIR


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "available_fonts" in data


def test_fonts_endpoint(client):
    response = client.get("/api/fonts")
    assert response.status_code == 200
    data = response.json()
    assert "fonts" in data
    font_names = [f["name"] for f in data["fonts"]]
    assert any("Cairo" in name for name in font_names) or any("Tajawal" in name for name in font_names)


def test_static_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "DZ Subtitles AI" in response.text


def test_render_api_mock(client, tmp_path):
    # Setup mock task folder in OUTPUT_DIR
    task_id = "test_unit_task"
    task_folder = OUTPUT_DIR / task_id
    os.makedirs(task_folder, exist_ok=True)

    # Copy sample tone
    sample_src = os.path.join("sample_data", "test_tone.mp3")
    if os.path.exists(sample_src):
        shutil.copy(sample_src, task_folder / "input.mp3")

        payload = {
            "task_id": task_id,
            "transcription_data": {
                "segments": [
                    {
                        "id": 0,
                        "start": 0.0,
                        "end": 2.0,
                        "text": "سلام عليكم خاوتنا",
                        "words": [
                            {"word": "سلام", "start": 0.0, "end": 0.6},
                            {"word": "عليكم", "start": 0.6, "end": 1.2},
                            {"word": "خاوتنا", "start": 1.2, "end": 2.0}
                        ]
                    }
                ]
            },
            "font_name": "Cairo",
            "font_size": 48,
            "primary_color": "#FFFFFF",
            "highlight_color": "#FFE600",
            "background_mode": "green_screen",
            "aspect_ratio": "9:16",
            "animation_style": "karaoke_pop"
        }

        response = client.post("/api/render", json=payload)
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["status"] == "success"
        assert "video_url" in res_data
        assert "ass_url" in res_data
        assert "srt_url" in res_data

        # Check file download endpoint
        dl_res = client.get(res_data["srt_url"])
        assert dl_res.status_code == 200
        assert "سلام عليكم خاوتنا" in dl_res.text

    # Cleanup
    shutil.rmtree(task_folder, ignore_errors=True)
