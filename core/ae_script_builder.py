"""
Adobe After Effects ExtendScript (.jsx) Generator for Algerian Darija & Viral Subtitles
Generates native After Effects compositions with fully editable keyframed text layers.
"""

import json
from typing import Dict, Any, List


class AfterEffectsScriptBuilder:
    def __init__(
        self,
        font_name: str = "Lalezar-Regular",
        font_size: int = 56,
        primary_color: str = "#FFFFFF",
        highlight_color: str = "#FFE600",
        animation_style: str = "letter_pop",
        words_per_line: int = 3,
        comp_width: int = 1080,
        comp_height: int = 1920,
        fps: float = 30.0,
        pos_y: int = 960
    ):
        self.font_name = font_name
        self.font_size = font_size
        self.primary_color = primary_color
        self.highlight_color = highlight_color
        self.animation_style = animation_style
        self.words_per_line = words_per_line
        self.comp_width = comp_width
        self.comp_height = comp_height
        self.fps = fps
        self.pos_y = pos_y

    def hex_to_rgb_norm(self, hex_code: str) -> List[float]:
        """Converts HEX string #RRGGBB to normalized [R, G, B] array (0.0 to 1.0) for After Effects."""
        hex_code = hex_code.lstrip("#")
        if len(hex_code) == 3:
            hex_code = "".join(c * 2 for c in hex_code)
        if len(hex_code) != 6:
            return [1.0, 1.0, 1.0]
        r = int(hex_code[0:2], 16) / 255.0
        g = int(hex_code[2:4], 16) / 255.0
        b = int(hex_code[4:6], 16) / 255.0
        return [round(r, 4), round(g, 4), round(b, 4)]

    def generate_jsx(self, transcription_data: Dict[str, Any], total_duration: float = 30.0) -> str:
        """
        Builds a complete, standalone ExtendScript (.jsx) file ready to run in Adobe After Effects.
        File > Scripts > Run Script File... creates a new comp with synchronized text layers.
        """
        segments = transcription_data.get("segments", [])
        pri_rgb = self.hex_to_rgb_norm(self.primary_color)
        hl_rgb = self.hex_to_rgb_norm(self.highlight_color)

        # Collect all words
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

        # Group words into chunks
        chunks: List[List[Dict[str, Any]]] = []
        current_chunk: List[Dict[str, Any]] = []
        for w in all_words:
            current_chunk.append(w)
            if len(current_chunk) >= self.words_per_line:
                chunks.append(current_chunk)
                current_chunk = []
        if current_chunk:
            chunks.append(current_chunk)

        # Calculate max comp duration
        max_time = total_duration
        if all_words:
            max_time = max(max_time, all_words[-1].get("end", 10.0) + 1.0)

        jsx_lines = [
            "// ============================================================================",
            "// DZ Subtitles AI - Adobe After Effects Import Script (.jsx)",
            "// Generated automatically for Adobe After Effects CC / 2020-2026",
            "// Instructions: Open After Effects -> File > Scripts > Run Script File...",
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
            f"    var compDuration = {round(max_time + 1.0, 2)};",
            f"    var compPosY = {self.pos_y};",
            f"    var fontSize = {self.font_size};",
            f"    var primaryColor = [{pri_rgb[0]}, {pri_rgb[1]}, {pri_rgb[2]}];",
            f"    var highlightColor = [{hl_rgb[0]}, {hl_rgb[1]}, {hl_rgb[2]}];",
            "",
            "    // Create main Comp",
            "    var comp = proj.items.addComp('DZ_Subtitles_Viral', compWidth, compHeight, 1.0, compDuration, compFps);",
            "    comp.bgColor = [0.05, 0.05, 0.07];",
            "",
            "    // Style parameters",
            f"    var animStyle = '{self.animation_style}';",
            ""
        ]

        # Generate layer for each chunk
        for chunk_idx, chunk in enumerate(chunks):
            if not chunk:
                continue
            chunk_text = " ".join(w.get("word", "") for w in chunk).replace("'", "\\'")
            chunk_start = round(chunk[0].get("start", 0.0), 3)
            chunk_end = round(chunk[-1].get("end", chunk_start + 1.5), 3)
            chunk_dur = max(0.5, chunk_end - chunk_start)

            var_name = f"textLayer_{chunk_idx + 1}"
            jsx_lines.extend([
                f"    // Chunk {chunk_idx + 1}: {chunk_text[:30]}",
                f"    var {var_name} = comp.layers.addText('{chunk_text}');",
                f"    {var_name}.inPoint = {chunk_start};",
                f"    {var_name}.outPoint = {chunk_end};",
                f"    var txtProp_{chunk_idx + 1} = {var_name}.property('Source Text');",
                f"    var txtDoc_{chunk_idx + 1} = txtProp_{chunk_idx + 1}.value;",
                f"    txtDoc_{chunk_idx + 1}.fontSize = fontSize;",
                f"    txtDoc_{chunk_idx + 1}.fillColor = primaryColor;",
                f"    txtDoc_{chunk_idx + 1}.applyStroke = true;",
                f"    txtDoc_{chunk_idx + 1}.strokeColor = [0, 0, 0];",
                f"    txtDoc_{chunk_idx + 1}.strokeWidth = 3.5;",
                f"    txtDoc_{chunk_idx + 1}.justification = ParagraphJustification.CENTER_JUSTIFY;",
                f"    txtProp_{chunk_idx + 1}.setValue(txtDoc_{chunk_idx + 1});",
                f"    {var_name}.property('Position').setValue([compWidth / 2, compPosY]);",
                ""
            ])

            # Apply Keyframe animations based on animation_style
            if "letter" in self.animation_style or self.animation_style in ("letter_pop", "letter_drop", "letter_rise"):
                # Add text animator for letter-by-letter reveal
                jsx_lines.extend([
                    f"    var anim_{chunk_idx + 1} = {var_name}.Text.Animators.addAnimator();",
                    f"    anim_{chunk_idx + 1}.name = 'Letter Pop Animator';",
                    f"    var scaleProp = anim_{chunk_idx + 1}.property('ADBE Text Animator Properties').addProperty('ADBE Text Scale 3D');",
                    f"    scaleProp.setValue([0, 0, 100]);",
                    f"    var selector = anim_{chunk_idx + 1}.property('ADBE Text Selectors').addProperty('ADBE Text Selector');",
                    f"    selector.property('Start').setValue(0);",
                    f"    var endProp = selector.property('End');",
                    f"    endProp.setValueAtTime({chunk_start}, 0);",
                    f"    endProp.setValueAtTime({round(chunk_start + min(1.0, chunk_dur * 0.8), 3)}, 100);",
                    ""
                ])
            else:
                # Spring pop scale keyframes
                jsx_lines.extend([
                    f"    var scaleProp_{chunk_idx + 1} = {var_name}.property('Scale');",
                    f"    scaleProp_{chunk_idx + 1}.setValueAtTime({chunk_start}, [90, 90, 100]);",
                    f"    scaleProp_{chunk_idx + 1}.setValueAtTime({round(chunk_start + 0.12, 3)}, [115, 115, 100]);",
                    f"    scaleProp_{chunk_idx + 1}.setValueAtTime({round(chunk_start + 0.24, 3)}, [100, 100, 100]);",
                    ""
                ])

        jsx_lines.extend([
            "    app.endUndoGroup();",
            "    alert('DZ Subtitles AI: Successfully imported ' + " + str(len(chunks)) + " + ' subtitle text layers into comp \"' + comp.name + '\"!');",
            "})();"
        ])

        return "\n".join(jsx_lines)
