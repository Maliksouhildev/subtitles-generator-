"""
Adobe After Effects ExtendScript (.jsx) and Timestamps Text Generator for Algerian Darija & Viral Subtitles.
Generates native After Effects compositions with fully editable, time-synced text layers,
pre-configured Letter-by-Letter animators, master hold-keyframe layer, and structured text exports.
"""

import json
import re
from typing import Dict, Any, List, Optional
from core.transcriber import bind_arabic_articles_to_latin


def format_ae_timecode(seconds: float) -> str:
    """Formats seconds to MM:SS.mmm timecode string."""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:06.3f}"


class AfterEffectsScriptBuilder:
    def __init__(
        self,
        font_name: str = "Cairo",
        font_size: int = 56,
        primary_color: str = "#FFFFFF",
        highlight_color: str = "#FFE600",
        animation_style: str = "letter_pop",
        words_per_line: int = 3,
        comp_width: int = 1080,
        comp_height: int = 1920,
        fps: float = 30.0,
        pos_y: int = 960,
        stroke_width: float = 6.0,
        ease_p1: Optional[List[float]] = None,
        ease_p2: Optional[List[float]] = None
    ):
        self.font_name = font_name
        self.font_size = font_size
        self.primary_color = primary_color
        self.highlight_color = highlight_color
        self.animation_style = animation_style
        self.words_per_line = min(4, max(2, words_per_line))
        self.comp_width = comp_width
        self.comp_height = comp_height
        self.fps = fps
        self.pos_y = pos_y
        self.stroke_width = max(4.0, float(stroke_width))
        self.ease_p1 = ease_p1 or [0.34, 1.56]
        self.ease_p2 = ease_p2 or [0.64, 1.00]

    def hex_to_rgb_norm(self, hex_code: str) -> List[float]:
        """Converts HEX string #RRGGBB to normalized [R, G, B] array (0.0 to 1.0) for After Effects."""
        hex_code = (hex_code or "#FFFFFF").lstrip("#")
        if len(hex_code) == 3:
            hex_code = "".join(c * 2 for c in hex_code)
        if len(hex_code) != 6:
            return [1.0, 1.0, 1.0]
        try:
            r = int(hex_code[0:2], 16) / 255.0
            g = int(hex_code[2:4], 16) / 255.0
            b = int(hex_code[4:6], 16) / 255.0
            return [round(r, 4), round(g, 4), round(b, 4)]
        except Exception:
            return [1.0, 1.0, 1.0]

    def extract_and_chunk_words(self, transcription_data: Dict[str, Any]) -> List[List[Dict[str, Any]]]:
        """Collects words with bound Arabic articles and chunks them based on words_per_line."""
        segments = transcription_data.get("segments", [])
        all_words: List[Dict[str, Any]] = []

        for seg in segments:
            words = seg.get("words", [])
            if words:
                all_words.extend(words)
            else:
                text = seg.get("text", "").strip()
                if text:
                    all_words.append({
                        "word": text,
                        "start": seg.get("start", 0.0),
                        "end": seg.get("end", 2.0)
                    })

        # Bind isolated Arabic articles (الـ, لـ, etc.) to following Latin words
        bound_words = bind_arabic_articles_to_latin(all_words)

        chunks: List[List[Dict[str, Any]]] = []
        current_chunk: List[Dict[str, Any]] = []
        for w in bound_words:
            current_chunk.append(w)
            if len(current_chunk) >= self.words_per_line:
                chunks.append(current_chunk)
                current_chunk = []
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def generate_jsx(self, transcription_data: Dict[str, Any], total_duration: float = 30.0) -> str:
        """
        Builds a complete, standalone ExtendScript (.jsx) file ready to run in Adobe After Effects.
        File > Scripts > Run Script File... creates a new comp with synchronized text layers,
        letter-by-letter animators, and a master hold-keyframe layer.
        """
        pri_rgb = self.hex_to_rgb_norm(self.primary_color)
        hl_rgb = self.hex_to_rgb_norm(self.highlight_color)
        chunks = self.extract_and_chunk_words(transcription_data)

        # Calculate max comp duration
        max_time = float(total_duration)
        if chunks and chunks[-1]:
            max_time = max(max_time, float(chunks[-1][-1].get("end", 10.0)) + 1.0)

        # Derived KeyframeEase influences for bouncy/spring curves
        inf_out = round(max(5.0, min(95.0, float(self.ease_p1[0]) * 100.0)), 1)
        inf_in = round(max(5.0, min(95.0, (1.0 - float(self.ease_p2[0])) * 100.0)), 1)

        safe_font = json.dumps(self.font_name or "Cairo")

        jsx_lines = [
            "// ============================================================================",
            "// DZ Subtitles AI - Adobe After Effects Import Script (.jsx)",
            "// Generated automatically for Adobe After Effects CC (2019-2026+)",
            "// Instructions:",
            "//   1. Open Adobe After Effects.",
            "//   2. Go to: File > Scripts > Run Script File...",
            "//   3. Select this .jsx file.",
            "//   4. A new composition 'DZ_Subtitles_Viral' is created with all text layers,",
            "//      exact millisecond timestamps, and customizable letter-by-letter animators!",
            "// Note: For native Arabic RTL text shaping in AE, ensure Type preferences are set:",
            "//   Edit > Preferences > Type > 'South Asian and Middle Eastern' (or Universal Engine).",
            "// ============================================================================",
            "(function() {",
            "    app.beginUndoGroup('Import DZ Subtitles AI Comp');",
            "",
            "    var proj = app.project;",
            "    if (!proj) {",
            "        proj = app.newProject();",
            "    }",
            "",
            f"    var compWidth = {self.comp_width};",
            f"    var compHeight = {self.comp_height};",
            f"    var compFps = {self.fps};",
            f"    var compDuration = {round(max_time + 0.5, 3)};",
            f"    var compPosY = {self.pos_y};",
            f"    var fontSize = {self.font_size};",
            f"    var fontName = {safe_font};",
            f"    var strokeWidth = {self.stroke_width};",
            f"    var primaryColor = [{pri_rgb[0]}, {pri_rgb[1]}, {pri_rgb[2]}];",
            f"    var highlightColor = [{hl_rgb[0]}, {hl_rgb[1]}, {hl_rgb[2]}];",
            "",
            "    // Create main Comp",
            "    var comp = proj.items.addComp('DZ_Subtitles_Viral', compWidth, compHeight, 1.0, compDuration, compFps);",
            "    comp.bgColor = [0.05, 0.05, 0.07];",
            "",
            "    // Helper: Style a TextDocument object with font, fill, stroke, and center alignment",
            "    function styleTextDoc(doc) {",
            "        doc.fontSize = fontSize;",
            "        doc.fillColor = primaryColor;",
            "        doc.applyStroke = true;",
            "        doc.strokeColor = [0, 0, 0];",
            "        doc.strokeWidth = strokeWidth;",
            "        if ('strokeOverFill' in doc) { doc.strokeOverFill = false; } // Fill over stroke",
            "        doc.justification = ParagraphJustification.CENTER_JUSTIFY;",
            "        try {",
            "            if (fontName && fontName !== '') { doc.font = fontName; }",
            "        } catch(e) {}",
            "        return doc;",
            "    }",
            "",
            "    // ========================================================================",
            "    // LAYER 1: MASTER SUBTITLE LAYER (Single Layer with Hold Keyframes)",
            "    // Edit all subtitles or apply global animators on ONE master layer!",
            "    // ========================================================================",
            "    var masterLayer = comp.layers.addText('');",
            "    masterLayer.name = '00_MASTER_SUBTITLES (Single Layer Hold Keyframes)';",
            "    masterLayer.inPoint = 0;",
            "    masterLayer.outPoint = compDuration;",
            "    masterLayer.property('Position').setValue([compWidth / 2, compPosY]);",
            "    var masterTxtProp = masterLayer.property('ADBE Text Properties').property('ADBE Text Document');",
            ""
        ]

        # Add hold keyframes to master layer
        for chunk_idx, chunk in enumerate(chunks):
            if not chunk:
                continue
            chunk_text = " ".join(w.get("word", "") for w in chunk).strip()
            chunk_start = round(float(chunk[0].get("start", 0.0)), 3)
            chunk_end = round(float(chunk[-1].get("end", chunk_start + 1.5)), 3)
            safe_text = json.dumps(chunk_text, ensure_ascii=False)

            jsx_lines.extend([
                f"    // Master Keyframe {chunk_idx + 1}",
                f"    var mDoc_{chunk_idx + 1} = masterTxtProp.value;",
                f"    mDoc_{chunk_idx + 1}.text = {safe_text};",
                f"    styleTextDoc(mDoc_{chunk_idx + 1});",
                f"    masterTxtProp.setValueAtTime({chunk_start}, mDoc_{chunk_idx + 1});",
                f"    try {{",
                f"        masterLayer.property('Marker').setValueAtTime({chunk_start}, new MarkerValue({safe_text}));",
                f"    }} catch(mErr) {{}}",
                ""
            ])

            # If gap to next chunk > 0.4s, clear text during silence
            if chunk_idx + 1 < len(chunks):
                next_start = round(float(chunks[chunk_idx + 1][0].get("start", chunk_end)), 3)
                if next_start - chunk_end > 0.35:
                    jsx_lines.extend([
                        f"    var mDocClear_{chunk_idx + 1} = masterTxtProp.value;",
                        f"    mDocClear_{chunk_idx + 1}.text = '';",
                        f"    masterTxtProp.setValueAtTime({chunk_end}, mDocClear_{chunk_idx + 1});",
                        ""
                    ])

        jsx_lines.extend([
            "    // Set all master text keyframes to HOLD interpolation",
            "    try {",
            "        for (var k = 1; k <= masterTxtProp.numKeys; k++) {",
            "            masterTxtProp.setInterpolationTypeAtKey(k, KeyframeInterpolationType.HOLD);",
            "        }",
            "    } catch(kErr) {}",
            "",
            "    // ========================================================================",
            "    // INDIVIDUAL CHUNK LAYERS (Isolated timing & Letter-by-Letter Animators)",
            "    // ========================================================================"
        ])

        # Generate individual layer for each chunk
        for chunk_idx, chunk in enumerate(chunks):
            if not chunk:
                continue
            chunk_text = " ".join(w.get("word", "") for w in chunk).strip()
            chunk_start = round(float(chunk[0].get("start", 0.0)), 3)
            chunk_end = round(float(chunk[-1].get("end", chunk_start + 1.5)), 3)
            chunk_dur = max(0.4, round(chunk_end - chunk_start, 3))
            safe_text = json.dumps(chunk_text, ensure_ascii=False)

            var_name = f"textLayer_{chunk_idx + 1}"
            layer_name = f"Sub_{chunk_idx + 1:02d} [{format_ae_timecode(chunk_start)}]"

            jsx_lines.extend([
                f"    // Chunk {chunk_idx + 1}: {chunk_text[:30]}",
                f"    var {var_name} = comp.layers.addText({safe_text});",
                f"    {var_name}.name = '{layer_name}';",
                f"    {var_name}.inPoint = {chunk_start};",
                f"    {var_name}.outPoint = {chunk_end};",
                f"    var txtProp_{chunk_idx + 1} = {var_name}.property('ADBE Text Properties').property('ADBE Text Document');",
                f"    var txtDoc_{chunk_idx + 1} = txtProp_{chunk_idx + 1}.value;",
                f"    styleTextDoc(txtDoc_{chunk_idx + 1});",
                f"    txtProp_{chunk_idx + 1}.setValue(txtDoc_{chunk_idx + 1});",
                f"    {var_name}.property('Position').setValue([compWidth / 2, compPosY]);",
                ""
            ])

            # Apply Keyframe animations based on animation_style
            if "letter" in self.animation_style or self.animation_style in ("letter_pop", "letter_drop", "letter_rise", "karaoke_pop"):
                # Clean, robust ExtendScript Text Animator for Letter-by-Letter reveal
                anim_time = round(min(0.65, chunk_dur * 0.75), 3)
                jsx_lines.extend([
                    f"    // Letter-by-Letter Reveal Animator for {var_name}",
                    f"    try {{",
                    f"        var textProps_{chunk_idx + 1} = {var_name}.property('ADBE Text Properties');",
                    f"        var animGroup_{chunk_idx + 1} = textProps_{chunk_idx + 1}.property('ADBE Text Animators');",
                    f"        var anim_{chunk_idx + 1} = animGroup_{chunk_idx + 1}.addProperty('ADBE Text Animator');",
                    f"        anim_{chunk_idx + 1}.name = 'Letter Pop Animator';",
                    f"        var animPropGroup_{chunk_idx + 1} = anim_{chunk_idx + 1}.property('ADBE Text Animator Properties');",
                    f"        var scaleProp_{chunk_idx + 1} = animPropGroup_{chunk_idx + 1}.addProperty('ADBE Text Scale 3D');",
                    f"        scaleProp_{chunk_idx + 1}.setValue([0, 0, 100]);",
                    f"        var opacityProp_{chunk_idx + 1} = animPropGroup_{chunk_idx + 1}.addProperty('ADBE Text Opacity');",
                    f"        opacityProp_{chunk_idx + 1}.setValue(0);",
                    f"        var selGroup_{chunk_idx + 1} = anim_{chunk_idx + 1}.property('ADBE Text Selectors');",
                    f"        var selector_{chunk_idx + 1} = selGroup_{chunk_idx + 1}.addProperty('ADBE Text Selector');",
                    f"        var endProp_{chunk_idx + 1} = selector_{chunk_idx + 1}.property('ADBE Text Percent End');",
                    f"        if (!endProp_{chunk_idx + 1}) endProp_{chunk_idx + 1} = selector_{chunk_idx + 1}.property('End');",
                    f"        if (endProp_{chunk_idx + 1}) {{",
                    f"            endProp_{chunk_idx + 1}.setValueAtTime({chunk_start}, 0);",
                    f"            endProp_{chunk_idx + 1}.setValueAtTime({round(chunk_start + anim_time, 3)}, 100);",
                    f"        }}",
                    f"    }} catch(animErr) {{}}",
                    ""
                ])

            # Also add KeyframeEase influence curve when bouncy_spring or specific easing is chosen
            if self.animation_style in ("bouncy_spring", "neon_glow", "color_flash"):
                jsx_lines.extend([
                    f"    // KeyframeEase bounce curve",
                    f"    try {{",
                    f"        var trScale_{chunk_idx + 1} = {var_name}.property('Scale');",
                    f"        trScale_{chunk_idx + 1}.setValueAtTime({chunk_start}, [90, 90, 100]);",
                    f"        trScale_{chunk_idx + 1}.setValueAtTime({round(chunk_start + 0.12, 3)}, [115, 115, 100]);",
                    f"        trScale_{chunk_idx + 1}.setValueAtTime({round(chunk_start + 0.24, 3)}, [100, 100, 100]);",
                    f"        var easeIn_{chunk_idx + 1} = new KeyframeEase(0, {inf_in});",
                    f"        var easeOut_{chunk_idx + 1} = new KeyframeEase(0, {inf_out});",
                    f"        trScale_{chunk_idx + 1}.setTemporalEaseAtKey(1, [new KeyframeEase(0, 33.3)], [easeOut_{chunk_idx + 1}]);",
                    f"        trScale_{chunk_idx + 1}.setTemporalEaseAtKey(2, [easeIn_{chunk_idx + 1}], [easeOut_{chunk_idx + 1}]);",
                    f"        trScale_{chunk_idx + 1}.setTemporalEaseAtKey(3, [easeIn_{chunk_idx + 1}], [new KeyframeEase(0, 33.3)]);",
                    f"    }} catch(easeErr) {{}}",
                    ""
                ])

        jsx_lines.extend([
            "    app.endUndoGroup();",
            "    alert('DZ Subtitles AI: Successfully created After Effects composition \"' + comp.name + '\" with ' + " + str(len(chunks)) + " + ' subtitle text layers and 1 Master Hold-Keyframe layer!');",
            "})();"
        ])

        return "\n".join(jsx_lines)

    def generate_timestamped_text(self, transcription_data: Dict[str, Any]) -> str:
        """
        Generates clean, beautifully formatted plain text with exact timecodes,
        ideal for direct copying into After Effects, Premiere Pro, DaVinci Resolve, or Final Cut.
        """
        chunks = self.extract_and_chunk_words(transcription_data)
        lines: List[str] = [
            "================================================================================",
            "DZ SUBTITLES AI - TIMESTAMPS & TEXT EXPORT FOR ADOBE AFTER EFFECTS / PREMIERE",
            "================================================================================",
            "Language: Algerian Darija & Latin Loanwords",
            f"Total Subtitle Blocks: {len(chunks)}",
            "",
            "--------------------------------------------------------------------------------",
            "SECTION 1: SUBTITLES BY PHRASE (Exact Start -> End Timestamps)",
            "--------------------------------------------------------------------------------"
        ]

        for idx, chunk in enumerate(chunks, 1):
            if not chunk:
                continue
            chunk_text = " ".join(w.get("word", "") for w in chunk).strip()
            chunk_start = float(chunk[0].get("start", 0.0))
            chunk_end = float(chunk[-1].get("end", chunk_start + 1.5))
            duration = chunk_end - chunk_start

            tc_start = format_ae_timecode(chunk_start)
            tc_end = format_ae_timecode(chunk_end)

            lines.append(f"[{idx:02d}] {tc_start} -> {tc_end} ({duration:.2f}s)")
            lines.append(f"     {chunk_text}")
            lines.append("")

        lines.extend([
            "--------------------------------------------------------------------------------",
            "SECTION 2: TAB-SEPARATED VALUES (TSV) - Ready to paste into AE / Excel / Sheets",
            "Format: Start\tEnd\tDuration\tSubtitle Text",
            "--------------------------------------------------------------------------------",
            "Start\tEnd\tDuration\tText"
        ])

        for chunk in chunks:
            if not chunk:
                continue
            chunk_text = " ".join(w.get("word", "") for w in chunk).strip()
            chunk_start = float(chunk[0].get("start", 0.0))
            chunk_end = float(chunk[-1].get("end", chunk_start + 1.5))
            lines.append(f"{format_ae_timecode(chunk_start)}\t{format_ae_timecode(chunk_end)}\t{chunk_end - chunk_start:.3f}\t{chunk_text}")

        lines.extend([
            "",
            "--------------------------------------------------------------------------------",
            "SECTION 3: DETAILED WORD-BY-WORD TIMESTAMPS (For Character/Word Keyframing)",
            "--------------------------------------------------------------------------------"
        ])

        for idx, chunk in enumerate(chunks, 1):
            if not chunk:
                continue
            chunk_text = " ".join(w.get("word", "") for w in chunk).strip()
            lines.append(f"Block #{idx:02d}: \"{chunk_text}\"")
            for w in chunk:
                w_text = w.get("word", "").strip()
                w_start = float(w.get("start", 0.0))
                w_end = float(w.get("end", w_start + 0.3))
                lines.append(f"  • {format_ae_timecode(w_start)} - {format_ae_timecode(w_end)} ({w_end - w_start:.2f}s) : {w_text}")
            lines.append("")

        lines.extend([
            "--------------------------------------------------------------------------------",
            "SECTION 4: PURE CLEAN TEXT (For Direct Copying into After Effects Text Layer)",
            "--------------------------------------------------------------------------------"
        ])
        for chunk in chunks:
            if chunk:
                lines.append(" ".join(w.get("word", "") for w in chunk).strip())

        return "\n".join(lines)
