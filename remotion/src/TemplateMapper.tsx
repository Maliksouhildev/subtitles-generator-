import React from "react";

import { interpolate, spring } from "remotion";

export interface WordToken {

  word: string;

  start: number;

  end: number;

}

export interface CaptionsStyleProps {

  font_name?: string;

  font_size?: number;

  primary_color?: string;

  highlight_color?: string;

  outline_color?: string;

  shadow_color?: string;

  outline_width?: number;

  shadow_depth?: number;

  margin_v?: number;

  words_per_line?: number;

  animation_style?: string;

  animation_speed?: number;

  sub_box_style?: "none" | "pill" | "box" | "shadow";

  sub_box_color?: string;

  sub_box_alpha?: number;

  ease_p1?: [number, number];

  ease_p2?: [number, number];

  cubic_bezier?: string;

}

export interface TemplateProps {

  chunk: { words: WordToken[]; start: number; end: number };

  currentTime: number;

  frame: number;

  fps: number;

  style: CaptionsStyleProps;

  isChunkRtl: boolean;

}

const ARABIC_REGEX = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;
const LATIN_REGEX = /[a-zA-Z]/;

// Helper: group continuous words into Latin vs Arabic runs to preserve correct BiDi boundary isolation
function groupScriptRuns(words: WordToken[]) {
  const runs: Array<{ isLatin: boolean; words: WordToken[] }> = [];
  let currentRun: WordToken[] = [];
  let currentIsLatin: boolean | null = null;
  for (const w of words) {
    const hasLatin = LATIN_REGEX.test(w.word);
    const hasArabic = ARABIC_REGEX.test(w.word);
    // A token belongs to a pure Latin run only if it has Latin chars and NO Arabic chars
    const isLatin = hasLatin && !hasArabic;
    if (currentIsLatin === null || isLatin === currentIsLatin) {
      currentRun.push(w);
      currentIsLatin = isLatin;
    } else {
      runs.push({ isLatin: currentIsLatin, words: currentRun });
      currentRun = [w];
      currentIsLatin = isLatin;
    }
  }
  if (currentRun.length > 0 && currentIsLatin !== null) {
    runs.push({ isLatin: currentIsLatin, words: currentRun });
  }
  return runs;
}

// 1. Hormozi Pop Template (Viral, high bounce, punchy highlight)

export const HormoziPopTemplate: React.FC<TemplateProps> = ({

  chunk,

  currentTime,

  frame,

  fps,

  style,

}) => {

  const fontSize = style.font_size || 58;

  const primaryColor = style.primary_color || "#FFFFFF";

  const highlightColor = style.highlight_color || "#FFE600";

  const outlineColor = style.outline_color || "#000000";

  const outlineWidth = style.outline_width ?? 3.5;

  const spd = style.animation_speed ?? 1.0;

  const runs = groupScriptRuns(chunk.words);

  return (

    <>

      {runs.map((run, rIdx) => {

        const strokeWidth = Math.max(7.5, Math.round(fontSize * 0.11));
        const textStroke = `${strokeWidth}px ${outlineColor}`;
        const textShadow = `
          -${strokeWidth}px -${strokeWidth}px 0 ${outlineColor},
           ${strokeWidth}px -${strokeWidth}px 0 ${outlineColor},
          -${strokeWidth}px  ${strokeWidth}px 0 ${outlineColor},
           ${strokeWidth}px  ${strokeWidth}px 0 ${outlineColor},
           0px ${strokeWidth + 3}px 0 #000000,
           3px ${strokeWidth + 4}px 0 #000000,
          -3px ${strokeWidth + 4}px 0 #000000,
           0px ${strokeWidth + 8}px 18px rgba(0, 0, 0, 0.95)
        `;

        const wordsContent = run.words.map((w, wIdx) => {
          const isSpoken = currentTime >= w.start && currentTime <= w.end;
          const wordStartFrame = Math.round(w.start * fps);
          const wordEndFrame = Math.round(w.end * fps);

          // Snappy Remotion spring pop with fast attack for the viral Hormozi look
          const popSpring = spring({
            fps,
            frame: Math.max(0, (frame - wordStartFrame) * spd),
            config: { damping: 10, mass: 0.4, stiffness: 220 },
          });

          // Smooth decay when active word finishes
          const decaySpring = spring({
            fps,
            frame: Math.max(0, (frame - wordEndFrame) * spd),
            config: { damping: 14, mass: 0.45, stiffness: 190 },
          });

          // Active word physically pops up to 1.28 on impact -> settles at 1.15
          const activeScale = interpolate(
            popSpring,
            [0, 0.4, 0.75, 1.0],
            [1.0, 1.28, 1.12, 1.15],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );

          let scale = 1.0;
          if (currentTime >= w.start && currentTime <= w.end) {
            scale = activeScale;
          } else if (currentTime > w.end && frame - wordEndFrame < 10) {
            scale = interpolate(decaySpring, [0, 1], [1.15, 1.0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
          }

          const color = isSpoken ? highlightColor : primaryColor;

          return (
            <span
              key={wIdx}
              style={{
                display: "inline-block",
                transform: `scale(${scale})`,
                transformOrigin: "center bottom",
                color,
                fontSize: `${fontSize}px`,
                fontWeight: 900,
                textShadow,
                WebkitTextStroke: textStroke,
                paintOrder: "stroke fill",
                letterSpacing: run.isLatin ? "1px" : "0.5px",
                lineHeight: 1.15,
                userSelect: "none",
                whiteSpace: "nowrap",
              }}
            >
              {w.word}
            </span>
          );
        });

        if (run.isLatin) {

          return (

            <span

              key={rIdx}

              dir="ltr"

              style={{

                display: "inline-flex",

                direction: "ltr",

                unicodeBidi: "isolate",

                alignItems: "center",

                gap: "8px",

                margin: "0 4px",

              }}

            >

              {wordsContent}

            </span>

          );

        }

        return (
          <span
            key={rIdx}
            dir="rtl"
            style={{
              display: "inline-flex",
              direction: "rtl",
              unicodeBidi: "isolate",
              alignItems: "center",
              gap: "8px",
              margin: "0 4px",
            }}
          >
            {wordsContent}
          </span>
        );

      })}

    </>

  );

};

// 2. Minimal Slide Template (Clean, modern upward slide with smooth opacity)

export const MinimalSlideTemplate: React.FC<TemplateProps> = ({

  chunk,

  currentTime,

  frame,

  fps,

  style,

}) => {

  const fontSize = style.font_size || 56;

  const primaryColor = style.primary_color || "#F8FAFC";

  const highlightColor = style.highlight_color || "#38BDF8";

  const outlineColor = style.outline_color || "#090D16";

  const spd = style.animation_speed ?? 1.0;

  const runs = groupScriptRuns(chunk.words);

  return (

    <>

      {runs.map((run, rIdx) => {

        const wordsContent = run.words.map((w, wIdx) => {

          const isSpoken = currentTime >= w.start && currentTime <= w.end;

          const wordStartFrame = Math.round(w.start * fps);

          const springProgress = spring({

            fps,

            frame: Math.max(0, (frame - wordStartFrame) * spd),

            config: { stiffness: 140, damping: 16, mass: 0.9 },

          });

          const translateY = isSpoken

            ? interpolate(springProgress, [0, 1], [16, 0])

            : 0;

          const opacity = isSpoken

            ? interpolate(springProgress, [0, 1], [0.3, 1.0])

            : 0.65;

          const color = isSpoken ? highlightColor : primaryColor;

          return (

            <span

              key={wIdx}

              style={{

                display: "inline-block",

                transform: `translateY(${translateY}px)`,

                opacity,

                color,

                fontSize: `${fontSize}px`,

                fontWeight: 800,

                textShadow: `0 4px 16px rgba(0,0,0,0.7), 0 0 20px ${isSpoken ? "rgba(56,189,248,0.4)" : "transparent"}`,

                WebkitTextStroke: `1.8px ${outlineColor}`,

                letterSpacing: run.isLatin ? "1px" : "0.5px",

                lineHeight: 1.15,

                userSelect: "none",

                whiteSpace: "nowrap",

              }}

            >

              {w.word}

            </span>

          );

        });

        if (run.isLatin) {

          return (

            <span key={rIdx} dir="ltr" style={{ display: "inline-flex", direction: "ltr", gap: "8px", margin: "0 4px" }}>

              {wordsContent}

            </span>

          );

        }

        return (
          <span
            key={rIdx}
            dir="rtl"
            style={{
              display: "inline-flex",
              direction: "rtl",
              unicodeBidi: "isolate",
              alignItems: "center",
              gap: "8px",
              margin: "0 4px",
            }}
          >
            {wordsContent}
          </span>
        );

      })}

    </>

  );

};

// 3. Cyber Glitch Template (Futuristic cyberpunk chromatic glow & micro-pulse)

export const CyberGlitchTemplate: React.FC<TemplateProps> = ({

  chunk,

  currentTime,

  frame,

  fps,

  style,

}) => {

  const fontSize = style.font_size || 58;

  const primaryColor = style.primary_color || "#E2E8F0";

  const highlightColor = style.highlight_color || "#00F2FE";

  const outlineColor = style.outline_color || "#05050A";

  const spd = style.animation_speed ?? 1.0;

  const runs = groupScriptRuns(chunk.words);

  return (

    <>

      {runs.map((run, rIdx) => {

        const wordsContent = run.words.map((w, wIdx) => {

          const isSpoken = currentTime >= w.start && currentTime <= w.end;

          const wordStartFrame = Math.round(w.start * fps);

          const springProgress = spring({

            fps,

            frame: Math.max(0, (frame - wordStartFrame) * spd),

            config: { stiffness: 280, damping: 10, mass: 0.5 },

          });

          const jitterX = isSpoken ? interpolate(springProgress, [0, 0.3, 0.6, 1], [3, -2, 1, 0]) : 0;

          const scale = isSpoken ? interpolate(springProgress, [0, 0.5, 1], [1.0, 1.25, 1.1]) : 1.0;

          const color = isSpoken ? highlightColor : primaryColor;

          const textShadow = isSpoken

            ? `2.5px 0 0 #FE0979, -2.5px 0 0 #00F2FE, 0 0 16px rgba(0, 242, 254, 0.8)`

            : `1.5px 1.5px 0 ${outlineColor}, 0 4px 10px rgba(0,0,0,0.8)`;

          return (

            <span

              key={wIdx}

              style={{

                display: "inline-block",

                transform: `translateX(${jitterX}px) scale(${scale})`,

                color,

                fontSize: `${fontSize}px`,

                fontWeight: 900,

                textShadow,

                WebkitTextStroke: `2.2px ${outlineColor}`,

                letterSpacing: run.isLatin ? "1.5px" : "0.5px",

                lineHeight: 1.15,

                userSelect: "none",

                whiteSpace: "nowrap",

              }}

            >

              {w.word}

            </span>

          );

        });

        if (run.isLatin) {

          return (

            <span key={rIdx} dir="ltr" style={{ display: "inline-flex", direction: "ltr", gap: "8px", margin: "0 4px" }}>

              {wordsContent}

            </span>

          );

        }

        return (
          <span
            key={rIdx}
            dir="rtl"
            style={{
              display: "inline-flex",
              direction: "rtl",
              unicodeBidi: "isolate",
              alignItems: "center",
              gap: "8px",
              margin: "0 4px",
            }}
          >
            {wordsContent}
          </span>
        );

      })}

    </>

  );

};

// 4. Comic Bounce Template (High rebound spring with alternating tilt angle)

export const ComicBounceTemplate: React.FC<TemplateProps> = ({

  chunk,

  currentTime,

  frame,

  fps,

  style,

}) => {

  const fontSize = style.font_size || 60;

  const primaryColor = style.primary_color || "#FFFFFF";

  const highlightColor = style.highlight_color || "#A3E635"; // Lime Punch

  const outlineColor = style.outline_color || "#000000";

  const outlineWidth = style.outline_width ?? 3.8;

  const spd = style.animation_speed ?? 1.0;

  const runs = groupScriptRuns(chunk.words);

  return (

    <>

      {runs.map((run, rIdx) => {

        const wordsContent = run.words.map((w, wIdx) => {

          const isSpoken = currentTime >= w.start && currentTime <= w.end;

          const wordStartFrame = Math.round(w.start * fps);

          const springProgress = spring({

            fps,

            frame: Math.max(0, (frame - wordStartFrame) * spd),

            config: { stiffness: 260, damping: 8, mass: 0.6 },

          });

          const tiltSign = wIdx % 2 === 0 ? -1 : 1;

          const rotateDeg = isSpoken ? interpolate(springProgress, [0, 0.4, 0.8, 1], [0, tiltSign * 4.5, tiltSign * -1.5, 0]) : 0;

          const scale = isSpoken ? interpolate(springProgress, [0, 0.4, 0.8, 1], [1.0, 1.38, 1.06, 1.14]) : 1.0;

          const color = isSpoken ? highlightColor : primaryColor;

          const textStroke = `${outlineWidth}px ${outlineColor}`;

          const textShadow = `

            3px 3px 0 ${outlineColor},

            4px 4px 0 rgba(0, 0, 0, 0.9)

          `;

          return (

            <span

              key={wIdx}

              style={{

                display: "inline-block",

                transform: `rotate(${rotateDeg}deg) scale(${scale})`,

                transformOrigin: "center bottom",

                color,

                fontSize: `${fontSize}px`,

                fontWeight: 900,

                textShadow,

                WebkitTextStroke: textStroke,

                letterSpacing: run.isLatin ? "1px" : "0.5px",

                lineHeight: 1.15,

                userSelect: "none",

                whiteSpace: "nowrap",

              }}

            >

              {w.word}

            </span>

          );

        });

        if (run.isLatin) {

          return (

            <span key={rIdx} dir="ltr" style={{ display: "inline-flex", direction: "ltr", gap: "8px", margin: "0 4px" }}>

              {wordsContent}

            </span>

          );

        }

        return (
          <span
            key={rIdx}
            dir="rtl"
            style={{
              display: "inline-flex",
              direction: "rtl",
              unicodeBidi: "isolate",
              alignItems: "center",
              gap: "8px",
              margin: "0 4px",
            }}
          >
            {wordsContent}
          </span>
        );

      })}

    </>

  );

};

// 5. Viral Punch Template (Aggressive instantaneous hook pop)

export const ViralPunchTemplate: React.FC<TemplateProps> = ({

  chunk,

  currentTime,

  frame,

  fps,

  style,

}) => {

  const fontSize = style.font_size || 60;

  const primaryColor = style.primary_color || "#FFFFFF";

  const highlightColor = style.highlight_color || "#FF3B30";

  const outlineColor = style.outline_color || "#000000";

  const outlineWidth = style.outline_width ?? 4.0;

  const spd = style.animation_speed ?? 1.0;

  const runs = groupScriptRuns(chunk.words);

  return (

    <>

      {runs.map((run, rIdx) => {

        const wordsContent = run.words.map((w, wIdx) => {

          const isSpoken = currentTime >= w.start && currentTime <= w.end;

          const wordStartFrame = Math.round(w.start * fps);

          const springProgress = spring({

            fps,

            frame: Math.max(0, (frame - wordStartFrame) * spd),

            config: { stiffness: 320, damping: 14, mass: 0.6 },

          });

          const scale = isSpoken ? interpolate(springProgress, [0, 0.3, 0.7, 1], [1.0, 1.45, 1.08, 1.15]) : 1.0;

          const color = isSpoken ? highlightColor : primaryColor;

          return (

            <span

              key={wIdx}

              style={{

                display: "inline-block",

                transform: `scale(${scale})`,

                transformOrigin: "center center",

                color,

                fontSize: `${fontSize}px`,

                fontWeight: 900,

                textShadow: `0 6px 18px rgba(0,0,0,0.9)`,

                WebkitTextStroke: `${outlineWidth}px ${outlineColor}`,

                letterSpacing: run.isLatin ? "1px" : "0.5px",

                lineHeight: 1.15,

                userSelect: "none",

                whiteSpace: "nowrap",

              }}

            >

              {w.word}

            </span>

          );

        });

        if (run.isLatin) {

          return (

            <span key={rIdx} dir="ltr" style={{ display: "inline-flex", direction: "ltr", gap: "8px", margin: "0 4px" }}>

              {wordsContent}

            </span>

          );

        }

        return (
          <span
            key={rIdx}
            dir="rtl"
            style={{
              display: "inline-flex",
              direction: "rtl",
              unicodeBidi: "isolate",
              alignItems: "center",
              gap: "8px",
              margin: "0 4px",
            }}
          >
            {wordsContent}
          </span>
        );

      })}

    </>

  );

};

// 6. Fade Editorial Template (Smooth documentary fade with subtle highlight)

export const FadeEditorialTemplate: React.FC<TemplateProps> = ({

  chunk,

  currentTime,

  frame,

  fps,

  style,

}) => {

  const fontSize = style.font_size || 54;

  const primaryColor = style.primary_color || "#E2E8F0";

  const highlightColor = style.highlight_color || "#FBBF24"; // Amber gold

  const outlineColor = style.outline_color || "#0F172A";

  const spd = style.animation_speed ?? 1.0;

  const runs = groupScriptRuns(chunk.words);

  return (

    <>

      {runs.map((run, rIdx) => {

        const wordsContent = run.words.map((w, wIdx) => {

          const isSpoken = currentTime >= w.start && currentTime <= w.end;

          const wordStartFrame = Math.round(w.start * fps);

          const springProgress = spring({
            fps,
            frame: Math.max(0, (frame - wordStartFrame) * spd),
            config: { stiffness: 180, damping: 12, mass: 0.5 },
          });

          const opacity = isSpoken ? interpolate(springProgress, [0, 1], [0.35, 1.0]) : 0.7;
          const scale = isSpoken ? interpolate(springProgress, [0, 0.4, 1], [1.0, 1.22, 1.08]) : 1.0;
          const color = isSpoken ? highlightColor : primaryColor;

          return (
            <span
              key={wIdx}
              style={{
                display: "inline-block",
                transform: `scale(${scale})`,
                transformOrigin: "center bottom",
                opacity,
                color,

                fontSize: `${fontSize}px`,

                fontWeight: 800,

                textShadow: `0 3px 12px rgba(0,0,0,0.8)`,

                WebkitTextStroke: `1.8px ${outlineColor}`,

                letterSpacing: run.isLatin ? "0.8px" : "0.4px",

                lineHeight: 1.15,

                userSelect: "none",

                whiteSpace: "nowrap",

              }}

            >

              {w.word}

            </span>

          );

        });

        if (run.isLatin) {

          return (

            <span key={rIdx} dir="ltr" style={{ display: "inline-flex", direction: "ltr", gap: "8px", margin: "0 4px" }}>

              {wordsContent}

            </span>

          );

        }

        return (
          <span
            key={rIdx}
            dir="rtl"
            style={{
              display: "inline-flex",
              direction: "rtl",
              unicodeBidi: "isolate",
              alignItems: "center",
              gap: "8px",
              margin: "0 4px",
            }}
          >
            {wordsContent}
          </span>
        );

      })}

    </>

  );

};

// 7. Badge Invert Template (Social media badge pill highlight)

export const BadgeInvertTemplate: React.FC<TemplateProps> = ({

  chunk,

  currentTime,

  frame,

  fps,

  style,

}) => {

  const fontSize = style.font_size || 54;

  const primaryColor = style.primary_color || "#FFFFFF";

  const highlightColor = style.highlight_color || "#FFE600";

  const outlineColor = style.outline_color || "#000000";

  const spd = style.animation_speed ?? 1.0;

  const runs = groupScriptRuns(chunk.words);

  return (

    <>

      {runs.map((run, rIdx) => {

        const wordsContent = run.words.map((w, wIdx) => {

          const isSpoken = currentTime >= w.start && currentTime <= w.end;

          const wordStartFrame = Math.round(w.start * fps);

          const springProgress = spring({

            fps,

            frame: Math.max(0, (frame - wordStartFrame) * spd),

            config: { stiffness: 240, damping: 12, mass: 0.6 },

          });

          const scale = isSpoken ? interpolate(springProgress, [0, 0.4, 1], [1.0, 1.18, 1.06]) : 1.0;

          const isLight = () => {

            const h = (highlightColor || "#FFE600").replace("#", "");

            const r = parseInt(h.substring(0, 2), 16) || 255;

            const g = parseInt(h.substring(2, 4), 16) || 230;

            const b = parseInt(h.substring(4, 6), 16) || 0;

            return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.55;

          };

          const badgeContrast = isLight() ? "#111111" : "#FFFFFF";

          return (

            <span

              key={wIdx}

              style={{

                display: "inline-flex",

                alignItems: "center",

                justifyContent: "center",

                transform: `scale(${scale})`,

                transformOrigin: "center center",

                color: isSpoken ? badgeContrast : primaryColor,

                backgroundColor: isSpoken ? highlightColor : "transparent",

                borderRadius: "8px",

                padding: isSpoken ? "2px 10px" : "2px 2px",

                fontSize: `${fontSize}px`,

                fontWeight: 800,

                textShadow: isSpoken ? "none" : `0 3px 8px rgba(0,0,0,0.8)`,

                WebkitTextStroke: isSpoken ? "none" : `2px ${outlineColor}`,

                letterSpacing: run.isLatin ? "1px" : "0.6px",

                lineHeight: 1.15,

                boxShadow: isSpoken ? "0 4px 12px rgba(0,0,0,0.35)" : "none",

                userSelect: "none",

                whiteSpace: "nowrap",

                transition: "background-color 0.08s ease, color 0.08s ease",

              }}

            >

              {w.word}

            </span>

          );

        });

        if (run.isLatin) {

          return (

            <span key={rIdx} dir="ltr" style={{ display: "inline-flex", direction: "ltr", gap: "8px", margin: "0 4px" }}>

              {wordsContent}

            </span>

          );

        }

        return (
          <span
            key={rIdx}
            dir="rtl"
            style={{
              display: "inline-flex",
              direction: "rtl",
              unicodeBidi: "isolate",
              alignItems: "center",
              gap: "8px",
              margin: "0 4px",
            }}
          >
            {wordsContent}
          </span>
        );

      })}

    </>

  );

};

// Arabic Shaping Engine for Remotion Subtitle Templates
const REMOTION_ARABIC_GLYPHS: Record<string, { iso: string; fin?: string; ini?: string; med?: string }> = {
  '\u0621': { iso: '\uFE80' },
  '\u0622': { iso: '\uFE81', fin: '\uFE82' },
  '\u0623': { iso: '\uFE83', fin: '\uFE84' },
  '\u0624': { iso: '\uFE85', fin: '\uFE86' },
  '\u0625': { iso: '\uFE87', fin: '\uFE88' },
  '\u0626': { iso: '\uFE89', fin: '\uFE8A', ini: '\uFE8B', med: '\uFE8C' },
  '\u0627': { iso: '\uFE8D', fin: '\uFE8E' },
  '\u0628': { iso: '\uFE8F', fin: '\uFE90', ini: '\uFE91', med: '\uFE92' },
  '\u0629': { iso: '\uFE93', fin: '\uFE94' },
  '\u062A': { iso: '\uFE95', fin: '\uFE96', ini: '\uFE97', med: '\uFE98' },
  '\u062B': { iso: '\uFE99', fin: '\uFE9A', ini: '\uFE9B', med: '\uFE9C' },
  '\u062C': { iso: '\uFE9D', fin: '\uFE9E', ini: '\uFE9F', med: '\uFEA0' },
  '\u062D': { iso: '\uFEA1', fin: '\uFEA2', ini: '\uFEA3', med: '\uFEA4' },
  '\u062E': { iso: '\uFEA5', fin: '\uFEA6', ini: '\uFEA7', med: '\uFEA8' },
  '\u062F': { iso: '\uFEA9', fin: '\uFEAA' },
  '\u0630': { iso: '\uFEAB', fin: '\uFEAC' },
  '\u0631': { iso: '\uFEAD', fin: '\uFEAE' },
  '\u0632': { iso: '\uFEAF', fin: '\uFEB0' },
  '\u0633': { iso: '\uFEB1', fin: '\uFEB2', ini: '\uFEB3', med: '\uFEB4' },
  '\u0634': { iso: '\uFEB5', fin: '\uFEB6', ini: '\uFEB7', med: '\uFEB8' },
  '\u0635': { iso: '\uFEB9', fin: '\uFEBA', ini: '\uFEBB', med: '\uFEBC' },
  '\u0636': { iso: '\uFEBD', fin: '\uFEBE', ini: '\uFEBF', med: '\uFEC0' },
  '\u0637': { iso: '\uFEC1', fin: '\uFEC2', ini: '\uFEC3', med: '\uFEC4' },
  '\u0638': { iso: '\uFEC5', fin: '\uFEC6', ini: '\uFEC7', med: '\uFEC8' },
  '\u0639': { iso: '\uFEC9', fin: '\uFECA', ini: '\uFECB', med: '\uFECC' },
  '\u063A': { iso: '\uFECD', fin: '\uFECE', ini: '\uFECF', med: '\uFED0' },
  '\u0640': { iso: '\u0640', fin: '\u0640', ini: '\u0640', med: '\u0640' },
  '\u0641': { iso: '\uFED1', fin: '\uFED2', ini: '\uFED3', med: '\uFED4' },
  '\u0642': { iso: '\uFED5', fin: '\uFED6', ini: '\uFED7', med: '\uFED8' },
  '\u0643': { iso: '\uFED9', fin: '\uFEDA', ini: '\uFEDB', med: '\uFEDC' },
  '\u0644': { iso: '\uFEDD', fin: '\uFEDE', ini: '\uFEDF', med: '\uFEE0' },
  '\u0645': { iso: '\uFEE1', fin: '\uFEE2', ini: '\uFEE3', med: '\uFEE4' },
  '\u0646': { iso: '\uFEE5', fin: '\uFEE6', ini: '\uFEE7', med: '\uFEE8' },
  '\u0647': { iso: '\uFEE9', fin: '\uFEEA', ini: '\uFEEB', med: '\uFEEC' },
  '\u0648': { iso: '\uFEED', fin: '\uFEEE' },
  '\u0649': { iso: '\uFEEF', fin: '\uFEF0', ini: '\uFEF3', med: '\uFEF4' },
  '\u064A': { iso: '\uFEF1', fin: '\uFEF2', ini: '\uFEF3', med: '\uFEF4' },
  '\u0671': { iso: '\uFB50', fin: '\uFB51' },
  '\u06A4': { iso: '\uFB6A', fin: '\uFB6B', ini: '\uFB6C', med: '\uFB6D' },
  '\u06AD': { iso: '\uFBD3', fin: '\uFBD4', ini: '\uFBD5', med: '\uFBD6' },
  '\u067E': { iso: '\uFB56', fin: '\uFB57', ini: '\uFB58', med: '\uFB59' },
  '\u0686': { iso: '\uFB7A', fin: '\uFB7B', ini: '\uFB7C', med: '\uFB7D' },
  '\u06AF': { iso: '\uFB92', fin: '\uFB93', ini: '\uFB94', med: '\uFB95' },
  '\u0698': { iso: '\uFB8A', fin: '\uFB8B' },
};

const REMOTION_LA_LIGATURES: Record<string, { iso: string; fin: string }> = {
  '\u0622': { iso: '\uFEF5', fin: '\uFEF6' },
  '\u0623': { iso: '\uFEF7', fin: '\uFEF8' },
  '\u0625': { iso: '\uFEF9', fin: '\uFEFA' },
  '\u0627': { iso: '\uFEFB', fin: '\uFEFC' },
  '\u0671': { iso: '\uFEFB', fin: '\uFEFC' },
};

export function shapeArabicWordToLetters(word: string): string[] {
  if (!word) return [];
  const isDiacritic = (c: string) => /[\u064B-\u065F\u0670]/.test(c);
  const rawChars = Array.from(word);
  const baseChars: string[] = [];
  const diacritics: string[] = [];

  for (let idx = 0; idx < rawChars.length; idx++) {
    const ch = rawChars[idx];
    if (isDiacritic(ch)) {
      if (diacritics.length > 0) {
        diacritics[diacritics.length - 1] += ch;
      }
    } else {
      baseChars.push(ch);
      diacritics.push('');
    }
  }

  const shaped: string[] = [];
  let i = 0;
  while (i < baseChars.length) {
    const ch = baseChars[i];
    const prevCh = i > 0 ? baseChars[i - 1] : null;
    const nextCh = i + 1 < baseChars.length ? baseChars[i + 1] : null;

    if (ch === '\u0644' && nextCh && REMOTION_LA_LIGATURES[nextCh]) {
      const prevEntry = prevCh ? REMOTION_ARABIC_GLYPHS[prevCh] : null;
      const connectsPrev = prevEntry && (prevEntry.ini || prevEntry.med);
      const lig = REMOTION_LA_LIGATURES[nextCh];
      const ligGlyph = (connectsPrev ? lig.fin : lig.iso) + diacritics[i] + diacritics[i + 1];
      shaped.push(ligGlyph);
      i += 2;
      continue;
    }

    const entry = REMOTION_ARABIC_GLYPHS[ch];
    if (!entry) {
      shaped.push(ch + diacritics[i]);
      i++;
      continue;
    }

    const prevEntry = prevCh ? REMOTION_ARABIC_GLYPHS[prevCh] : null;
    const nextEntry = nextCh ? REMOTION_ARABIC_GLYPHS[nextCh] : null;

    const connectsPrev = prevEntry && (prevEntry.ini || prevEntry.med) && (entry.fin || entry.med);
    const connectsNext = nextEntry && (entry.ini || entry.med) && (nextEntry.fin || nextEntry.med);

    let glyph = entry.iso || ch;
    if (connectsPrev && connectsNext && entry.med) {
      glyph = entry.med;
    } else if (connectsPrev && entry.fin) {
      glyph = entry.fin;
    } else if (connectsNext && entry.ini) {
      glyph = entry.ini;
    }
    shaped.push(glyph + diacritics[i]);
    i++;
  }
  return shaped;
}

// 8. Cumulative Fill Template (Progressive word coloring where words stay highlighted)
export const CumulativeFillTemplate: React.FC<TemplateProps> = ({
  chunk,
  currentTime,
  frame,
  fps,
  style,
}) => {
  const fontSize = style.font_size || 54;
  const primaryColor = style.primary_color || "#FFFFFF";
  const highlightColor = style.highlight_color || "#FFE600";
  const outlineColor = style.outline_color || "#000000";
  const spd = style.animation_speed ?? 1.0;

  const runs = groupScriptRuns(chunk.words);

  return (
    <>
      {runs.map((run, rIdx) => {
        const wordsContent = run.words.map((w, wIdx) => {
          const isSpoken = currentTime >= w.start && currentTime <= w.end;
          const isPastSpoken = currentTime > w.end;
          const isColored = isSpoken || isPastSpoken;
          const wordStartFrame = Math.round(w.start * fps);

          const springProgress = spring({
            fps,
            frame: Math.max(0, (frame - wordStartFrame) * spd),
            config: { stiffness: 280, damping: 14, mass: 0.6 },
          });

          const scale = isSpoken
            ? interpolate(springProgress, [0, 0.4, 1], [1.0, 1.25, 1.08])
            : 1.0;

          return (
            <span
              key={wIdx}
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                transform: `scale(${scale})`,
                transformOrigin: "center center",
                color: isColored ? highlightColor : primaryColor,
                fontSize: `${fontSize}px`,
                fontWeight: 900,
                textShadow: isColored
                  ? `0 2px 10px ${highlightColor}66`
                  : `0 3px 8px rgba(0,0,0,0.8)`,
                WebkitTextStroke: `2px ${outlineColor}`,
                letterSpacing: run.isLatin ? "1px" : "0px",
                lineHeight: 1.15,
                userSelect: "none",
                whiteSpace: "nowrap",
                transition: "color 0.08s ease",
              }}
            >
              {w.word}
            </span>
          );
        });

        if (run.isLatin) {
          return (
            <span key={rIdx} dir="ltr" style={{ display: "inline-flex", direction: "ltr", gap: "8px", margin: "0 4px" }}>
              {wordsContent}
            </span>
          );
        }
        return (
          <span
            key={rIdx}
            dir="rtl"
            style={{
              display: "inline-flex",
              direction: "rtl",
              unicodeBidi: "isolate",
              alignItems: "center",
              gap: "8px",
              margin: "0 4px",
            }}
          >
            {wordsContent}
          </span>
        );
      })}
    </>
  );
};

// 9. Letter Pop Template (Kinetic letter-by-letter reveal with contextual Arabic cursive shaping)
export const LetterPopTemplate: React.FC<TemplateProps> = ({
  chunk,
  currentTime,
  frame,
  fps,
  style,
}) => {
  const fontSize = style.font_size || 54;
  const primaryColor = style.primary_color || "#FFFFFF";
  const highlightColor = style.highlight_color || "#FFE600";
  const outlineColor = style.outline_color || "#000000";
  const spd = style.animation_speed ?? 1.0;

  const runs = groupScriptRuns(chunk.words);

  return (
    <>
      {runs.map((run, rIdx) => {
        const wordsContent = run.words.map((w, wIdx) => {
          const isSpoken = currentTime >= w.start && currentTime <= w.end;
          const wordStartFrame = Math.round(w.start * fps);
          const isArabicWord = /[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]/.test(w.word);

          if (!isSpoken) {
            return (
              <span
                key={wIdx}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: primaryColor,
                  fontSize: `${fontSize}px`,
                  fontWeight: 900,
                  textShadow: `0 3px 8px rgba(0,0,0,0.8)`,
                  WebkitTextStroke: `2px ${outlineColor}`,
                  letterSpacing: isArabicWord ? "0px" : "1px",
                  lineHeight: 1.15,
                  userSelect: "none",
                  whiteSpace: "nowrap",
                }}
              >
                {w.word}
              </span>
            );
          }

          const letters = isArabicWord ? shapeArabicWordToLetters(w.word) : Array.from(w.word);

          return (
            <span
              key={wIdx}
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: `${fontSize}px`,
                fontWeight: 900,
                color: highlightColor,
                WebkitTextStroke: `2px ${outlineColor}`,
                textShadow: `0 3px 12px ${highlightColor}88`,
                letterSpacing: isArabicWord ? "0px" : "1px",
                lineHeight: 1.15,
                userSelect: "none",
                whiteSpace: "nowrap",
                direction: isArabicWord ? "rtl" : "ltr",
              }}
            >
              {letters.map((ch, cIdx) => {
                const staggerFrames = Math.round(cIdx * (2.2 / spd));
                const letterFrame = Math.max(0, (frame - wordStartFrame) * spd - staggerFrames);
                const spr = spring({
                  fps,
                  frame: letterFrame,
                  config: { stiffness: 320, damping: 16, mass: 0.5 },
                });
                const scale = interpolate(spr, [0, 0.5, 1], [0.15, 1.32, 1.0]);
                const opacity = interpolate(spr, [0, 0.2, 1], [0, 1, 1]);

                return (
                  <span
                    key={cIdx}
                    style={{
                      display: "inline-block",
                      transform: `scale(${scale})`,
                      opacity,
                      transformOrigin: "center bottom",
                      margin: 0,
                      padding: 0,
                      letterSpacing: isArabicWord ? "0px" : "inherit",
                    }}
                  >
                    {ch}
                  </span>
                );
              })}
            </span>
          );
        });

        if (run.isLatin) {
          return (
            <span key={rIdx} dir="ltr" style={{ display: "inline-flex", direction: "ltr", gap: "8px", margin: "0 4px" }}>
              {wordsContent}
            </span>
          );
        }
        return (
          <span
            key={rIdx}
            dir="rtl"
            style={{
              display: "inline-flex",
              direction: "rtl",
              unicodeBidi: "isolate",
              alignItems: "center",
              gap: "8px",
              margin: "0 4px",
            }}
          >
            {wordsContent}
          </span>
        );
      })}
    </>
  );
};

// Parameterized Template Registry

export const TEMPLATE_REGISTRY: Record<string, React.FC<TemplateProps>> = {

  "hormozi-pop": HormoziPopTemplate,

  "karaoke_pop": HormoziPopTemplate,

  "minimal-slide": MinimalSlideTemplate,

  "minimal_slide": MinimalSlideTemplate,

  "smooth-slide": MinimalSlideTemplate,

  "smooth_slide": MinimalSlideTemplate,

  "cyber-glitch": CyberGlitchTemplate,

  "cyber_glitch": CyberGlitchTemplate,

  "cyber-pulse": CyberGlitchTemplate,

  "neon_glow": CyberGlitchTemplate,

  "comic-bounce": ComicBounceTemplate,

  "comic_bounce": ComicBounceTemplate,

  "bouncy_spring": ComicBounceTemplate,

  "viral-punch": ViralPunchTemplate,

  "viral_punch": ViralPunchTemplate,

  "typewriter_pop": ViralPunchTemplate,

  "fade-editorial": FadeEditorialTemplate,

  "fade_editorial": FadeEditorialTemplate,

  "fade_highlight": FadeEditorialTemplate,

  "classic_fade": FadeEditorialTemplate,

  "classic_line": FadeEditorialTemplate,

  "badge-invert": BadgeInvertTemplate,

  "badge_invert": BadgeInvertTemplate,

  "box_highlight": BadgeInvertTemplate,

  "letter_pop": LetterPopTemplate,

  "letter-pop": LetterPopTemplate,

  "letter_drop": LetterPopTemplate,

  "letter_rise": LetterPopTemplate,

  "cumulative_fill": CumulativeFillTemplate,

  "cumulative-fill": CumulativeFillTemplate,

  "cumulative_pop": CumulativeFillTemplate,

  "cumulative_glow": CumulativeFillTemplate,

  "word_reveal": MinimalSlideTemplate,

  "word-reveal": MinimalSlideTemplate,

};

export const DEFAULT_TEMPLATE_ID = "hormozi-pop";

export function getTemplateComponent(templateId?: string): React.FC<TemplateProps> {

  const cleanId = (templateId || "").trim().toLowerCase();

  return TEMPLATE_REGISTRY[cleanId] || TEMPLATE_REGISTRY[DEFAULT_TEMPLATE_ID];

}

