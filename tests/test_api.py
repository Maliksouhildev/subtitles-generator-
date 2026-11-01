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
    assert "phoneDevice" in response.text
    assert "lang-switch-group" in response.text
    assert "themeToggleBtn" in response.text
    assert "safeZoneGuide" in response.text
    assert "subcol-phone-sim" in response.text
    assert "subcol-controls" in response.text
    assert 'data-platform="tiktok"' in response.text
    assert 'data-platform="reels"' in response.text
    assert 'data-platform="shorts"' in response.text

    # Verify zero emojis in HTML markup
def test_translations_completeness():
    import re
    from pathlib import Path
    base_dir = Path(__file__).resolve().parent.parent
    html_file = base_dir / "web" / "static" / "index.html"
    js_file = base_dir / "web" / "static" / "app.js"
    css_file = base_dir / "web" / "static" / "style.css"

    html_content = html_file.read_text(encoding="utf-8")
    js_content = js_file.read_text(encoding="utf-8")
    css_content = css_file.read_text(encoding="utf-8")

    # Verify zero emojis across all static files
    forbidden_emojis = ["⚡", "📱", "🎨", "🚀", "🌊", "🔲", "🎬", "🟩", "⬛", "🟦", "🎯", "🇩🇿", "🇸🇦", "🇫🇷", "🇬🇧", "✅"]
    for file_name, text in [("index.html", html_content), ("app.js", js_content), ("style.css", css_content)]:
        for emoji in forbidden_emojis:
            assert emoji not in text, f"Emoji {emoji} found in {file_name}"

    # Extract all data-i18n keys
    keys = re.findall(r'data-i18n="([^"]+)"', html_content)
    assert len(keys) > 15, "Expected data-i18n keys in index.html"

    # Extract TRANSLATIONS sections
    en_match = re.search(r'en:\s*\{([^}]+)\}', js_content)
    fr_match = re.search(r'fr:\s*\{([^}]+)\}', js_content)
    ar_match = re.search(r'ar:\s*\{([^}]+)\}', js_content)
    assert en_match and fr_match and ar_match

    en_keys = set(re.findall(r'([a-zA-Z0-9_]+)\s*:', en_match.group(1)))
    fr_keys = set(re.findall(r'([a-zA-Z0-9_]+)\s*:', fr_match.group(1)))
    ar_keys = set(re.findall(r'([a-zA-Z0-9_]+)\s*:', ar_match.group(1)))

    for k in keys:
        assert k in en_keys, f"Key {k} missing from EN translations"
        assert k in fr_keys, f"Key {k} missing from FR translations"
        assert k in ar_keys, f"Key {k} missing from AR translations"



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
            "animation_style": "karaoke_pop",
            "sub_box_style": "pill",
            "sub_box_color": "#223344",
            "sub_box_alpha": 0.85
        }

        response = client.post("/api/render", json=payload)
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["status"] == "success"
        assert "video_url" in res_data
        assert "ass_url" in res_data
        assert "srt_url" in res_data
        assert "remotion_url" in res_data

        # Check Remotion props file download
        remotion_res = client.get(res_data["remotion_url"])
        assert remotion_res.status_code == 200
        remotion_data = remotion_res.json()
        assert "transcription" in remotion_data
        assert remotion_data["style"]["animation_style"] == "karaoke_pop"

        # Check file download endpoint
        dl_res = client.get(res_data["srt_url"])
        assert dl_res.status_code == 200
        assert "سلام عليكم خاوتنا" in dl_res.text

    # Cleanup
    shutil.rmtree(task_folder, ignore_errors=True)


def test_custom_dropdowns_and_rtl_preview():
    from pathlib import Path
    base_dir = Path(__file__).resolve().parent.parent
    html_content = (base_dir / "web" / "static" / "index.html").read_text(encoding="utf-8")
    js_content = (base_dir / "web" / "static" / "app.js").read_text(encoding="utf-8")
    css_content = (base_dir / "web" / "static" / "style.css").read_text(encoding="utf-8")

    # Verify default preview text contains authentic Algerian Darija words
    assert "السيارة" in html_content
    assert "تاعي" in html_content
    assert "الشخصية" in html_content
    assert 'dir="rtl"' in html_content

    # Verify universal custom dropdown engine and preview cycle in app.js
    assert "enhanceSelectsToComicDropdowns" in js_content
    assert "syncAllCustomDropdowns" in js_content
    assert "stepPreviewCycle" in js_content

    # Verify CSS custom dropdown styling
    assert ".comic-dropdown-option" in css_content
    assert ".custom-select-wrap" in css_content


def test_presets_api_and_persistence(client, tmp_path):
    # Test GET presets initially
    res_get = client.get("/api/presets")
    assert res_get.status_code == 200
    assert isinstance(res_get.json(), list)

    # Test POST custom preset
    custom_preset = [
        {
            "id": "preset_test_viral",
            "name": "My Test Viral Style",
            "settings": {
                "font": "Lalezar",
                "fontSize": 62,
                "primary": "#FFFFFF",
                "highlight": "#FFE600",
                "anim": "karaoke_pop",
                "speed": 1.2,
                "words": 3,
                "subBox": "pill",
                "boxColor": "#000000",
                "boxAlpha": 0.8,
                "posY": 920
            }
        }
    ]
    res_post = client.post("/api/presets", json=custom_preset)
    assert res_post.status_code == 200
    data = res_post.json()
    assert data["status"] == "success"
    assert data["count"] == 1

    # Verify retrieval
    res_verify = client.get("/api/presets")
    assert res_verify.status_code == 200
    presets_list = res_verify.json()
    assert len(presets_list) >= 1
    assert any(p["id"] == "preset_test_viral" for p in presets_list)

