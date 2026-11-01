from pathlib import Path
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
        assert "ae_url" in res_data

        # Check After Effects JSX script download
        ae_res = client.get(res_data["ae_url"])
        assert ae_res.status_code == 200
        assert "app.beginUndoGroup" in ae_res.text
        assert "addComp" in ae_res.text
        assert "DZ_Subtitles_Viral" in ae_res.text

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

    # Verify Ease graph, After Effects and letter animation components
    assert "easeCanvas" in html_content
    assert "sub-resize-handle" in html_content
    assert "downloadAeBtn" in html_content
    assert ".opt-box-demo" in css_content
    assert "letterPopAnim" in css_content


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

def test_keyframe_ease_editor_and_letter_animations():
    from pathlib import Path
    base_dir = Path(__file__).resolve().parent.parent
    html_file = base_dir / "web" / "static" / "index.html"
    css_file = base_dir / "web" / "static" / "style.css"
    js_file = base_dir / "web" / "static" / "app.js"
    remotion_file = base_dir / "remotion" / "src" / "TemplateMapper.tsx"

    html = html_file.read_text(encoding="utf-8")
    css = css_file.read_text(encoding="utf-8")
    js = js_file.read_text(encoding="utf-8")
    remotion = remotion_file.read_text(encoding="utf-8")

    # 1. Verify all new animation options exist in visual dropdown and select
    for anim in ["cumulative_fill", "letter_pop", "letter_drop", "letter_rise", "word_reveal"]:
        assert f'data-value="{anim}"' in html, f"Animation {anim} missing from animDropdownPanel"
        assert f'value="{anim}"' in html, f"Animation {anim} missing from animationStyle select"

    # 2. Verify interactive After Effects Style Ease Graph & Live Preview
    assert 'id="easeCanvas"' in html
    assert 'id="easeLivePreviewWord"' in html
    assert 'id="easeCoordsReadout"' in html
    assert 'id="easeGraphContainer"' in html
    assert 'grid-col-full' in html

    # 3. Verify Phone Simulation is aligned at top without dead space
    assert 'align-items: flex-start;' in css
    assert '.phone-frame-wrapper' in css

    # 4. Verify JS handles draggable keyframes and updates --anim-ease
    assert 'evalCubicBezier' in js
    assert 'updateAnimEaseProperty' in js
    assert 'easeP1' in js and 'easeP2' in js
    assert 'fromCanvasCoords' in js

    # 5. Verify Remotion Template registry maps word_reveal
    assert '"word_reveal":' in remotion

def test_language_adaptive_fonts_and_deduplicated_animations():
    from pathlib import Path
    import re
    base_dir = Path(__file__).resolve().parent.parent
    html_file = base_dir / "web" / "static" / "index.html"
    js_file = base_dir / "web" / "static" / "app.js"

    html = html_file.read_text(encoding="utf-8")
    js = js_file.read_text(encoding="utf-8")

    # 1. Verify 20 Arabic and 20 Latin fonts are present in index.html and app.js
    assert 'id="fontGroupArabic"' in html
    assert 'id="fontGroupLatin"' in html
    assert "ARABIC_FONTS" in js
    assert "LATIN_FONTS" in js
    assert "updateAdaptiveFontList" in js

    # Count options in Arabic and Latin optgroups
    arabic_opts = re.findall(r'<optgroup label="[^"]*Arabic[^"]*"[\s\S]*?<\/optgroup>', html)
    latin_opts = re.findall(r'<optgroup label="[^"]*Latin[^"]*"[\s\S]*?<\/optgroup>', html)
    assert len(arabic_opts) == 1
    assert len(latin_opts) == 1

    arabic_fonts = re.findall(r'<option value="([^"]+)"', arabic_opts[0])
    latin_fonts = re.findall(r'<option value="([^"]+)"', latin_opts[0])

    assert len(arabic_fonts) >= 20, f"Expected >= 20 Arabic fonts, got {len(arabic_fonts)}"
    assert len(latin_fonts) >= 20, f"Expected >= 20 Latin fonts, got {len(latin_fonts)}"

    # Check key viral fonts
    for f in ["Lalezar", "Cairo", "Tajawal", "Changa", "Almarai", "Amiri", "El Messiri"]:
        assert f in arabic_fonts
    for f in ["Montserrat", "Anton", "Bebas Neue", "Poppins", "Inter", "Oswald", "Outfit"]:
        assert f in latin_fonts

    # 2. Verify clones have been removed from visual animation dropdown
    m_dropdown = re.search(r'<div class="custom-dropdown-panel[^"]*" id="animDropdownPanel"[^>]*>([\s\S]*?)<\/div>\s*<select id="animationStyle"', html)
    assert m_dropdown
    dropdown_anims = re.findall(r'data-value="([^"]+)"', m_dropdown.group(1))

    clones = ["bouncy_spring", "box_highlight", "classic_line", "neon_glow"]
    for clone in clones:
        assert clone not in dropdown_anims, f"Clone {clone} should be removed from animDropdownPanel"

    # Distinct unique animations remain
    for distinct in ["karaoke_pop", "cumulative_fill", "letter_pop", "letter_drop", "letter_rise", "minimal_slide", "cyber_glitch", "comic_bounce", "viral_punch", "fade_editorial", "badge_invert", "color_flash", "word_reveal"]:
        assert distinct in dropdown_anims

    # 3. Verify Arabic font labels and live previews contain authentic Arabic script
    for ar_word in ["لاليزار", "كايرو", "تجوال", "المراعي", "أميري", "شانغا", "المسيري"]:
        assert ar_word in html
        assert ar_word in js

    assert "createFontOptionContent" in js
    assert "font-opt-preview-badge" in js
    assert ".font-opt-preview-badge.font-arabic-sample" in (base_dir / "web" / "static" / "style.css").read_text(encoding="utf-8")



def test_arabic_cursive_letter_shaping():
    """Verify that Arabic letter-by-letter kinetic animations preserve authentic cursive shapes."""
    js_file = Path("web/static/app.js")
    css_file = Path("web/static/style.css")
    remotion_file = Path("remotion/src/TemplateMapper.tsx")

    js = js_file.read_text(encoding="utf-8")
    css = css_file.read_text(encoding="utf-8")
    remotion = remotion_file.read_text(encoding="utf-8")

    # 1. Verify shapeArabicWordToLetters function is present in app.js and remotion
    assert "function shapeArabicWordToLetters" in js
    assert "export function shapeArabicWordToLetters" in remotion
    assert "LetterPopTemplate" in remotion
    assert "CumulativeFillTemplate" in remotion

    # 2. Verify kinetic letter animations apply arabic-letter class in app.js
    assert "isArabicWord ? shapeArabicWordToLetters(wordText) : Array.from(wordText)" in js
    assert "arabic-letter" in js

    # 3. Verify CSS rules for arabic-letter preserving cursive continuity
    assert ".sub-letter.arabic-letter" in css
    assert "letter-spacing: 0" in css
    assert "direction: rtl" in css

    # 4. Verify Node.js execution of shapeArabicWordToLetters on Darija Arabic words
    import subprocess
    node_cmd = [
        "node", "-e",
        '''
        const fs = require("fs");
        const code = fs.readFileSync("web/static/app.js", "utf8");
        const start = code.indexOf("const ARABIC_GLYPHS =");
        const end = code.indexOf("// LIVE SUBTITLE PREVIEW IN PHONE SIMULATION");
        const block = code.substring(start, end) + "\\nmodule.exports = { shapeArabicWordToLetters };";
        fs.writeFileSync("temp_test_eval.js", block, "utf8");
        const { shapeArabicWordToLetters } = require("./temp_test_eval.js");

        const ta3i = shapeArabicWordToLetters("تاعي");
        if (ta3i[0] !== "\\uFE97" || ta3i[1] !== "\\uFE8E" || ta3i[2] !== "\\uFECB" || ta3i[3] !== "\\uFEF2") {
            process.exit(1);
        }

        const sayara = shapeArabicWordToLetters("السيارة");
        if (sayara[2] !== "\\uFEB4" || sayara[3] !== "\\uFEF4") {
            process.exit(2);
        }

        const chakhsiya = shapeArabicWordToLetters("الشخصية");
        if (chakhsiya[2] !== "\\uFEB8" || chakhsiya[6] !== "\\uFE94") {
            process.exit(3);
        }

        fs.unlinkSync("temp_test_eval.js");
        process.stdout.write("OK");
        '''
    ]
    res = subprocess.run(node_cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Node shaper test failed: {res.stderr}"
    assert "OK" in res.stdout


def test_fixed_phone_preview_and_ae_graph_integration():
    """Verify fixed phone preview styles, AE graph easing, and AE JSX export."""
    with open("web/static/style.css", "r", encoding="utf-8") as f:
        css = f.read()

    # Fixed phone preview
    assert "position: sticky" in css
    assert "overflow: hidden" in css
    assert "--anim-ease:" in css
    assert "var(--anim-ease" in css
    assert "ease-canvas-wrap" in css
    assert "anim-bouncy_spring" in css

    # AE Script Builder KeyframeEase influence
    from core.ae_script_builder import AfterEffectsScriptBuilder
    builder = AfterEffectsScriptBuilder(
        font_name="Cairo",
        font_size=56,
        primary_color="#FFFFFF",
        highlight_color="#FFE600",
        animation_style="bouncy_spring",
        words_per_line=3,
        ease_p1=[0.34, 1.56],
        ease_p2=[0.64, 1.00]
    )
    jsx = builder.generate_jsx({
        "segments": [{
            "start": 0.0,
            "end": 2.0,
            "text": "السيارة تاعي",
            "words": [
                {"word": "السيارة", "start": 0.0, "end": 1.0},
                {"word": "تاعي", "start": 1.0, "end": 2.0}
            ]
        }]
    })
    assert "KeyframeEase" in jsx
    assert "setTemporalEaseAtKey" in jsx
    assert "34.0" in jsx or "36.0" in jsx  # Influences derived from ease_p1/p2

    # RenderRequest schema
    from server import RenderRequest
    req = RenderRequest(
        task_id="test_task",
        ease_p1=[0.25, 1.0],
        ease_p2=[0.50, 1.0],
        cubic_bezier="cubic-bezier(0.25, 1.00, 0.50, 1.00)"
    )
    assert req.ease_p1 == [0.25, 1.0]
    assert req.cubic_bezier == "cubic-bezier(0.25, 1.00, 0.50, 1.00)"

