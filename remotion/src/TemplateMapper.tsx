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
}

export interface TemplateProps {
  chunk: { words: WordToken[]; start: number; end: number };
  currentTime: number;
  frame: number;
  fps: number;
  style: CaptionsStyleProps;
  isChunkRtl: boolean;
}

const LATIN_REGEX = /[a-zA-Z]/;

// Helper: group continuous words into Latin vs Arabic runs to preserve correct BiDi boundary isolation
function groupScriptRuns(words: WordToken[]) {
  const runs: Array<{ isLatin: boolean; words: WordToken[] }> = [];
  let currentRun: WordToken[] = [];
  let currentIsLatin: boolean | null = null;

  for (const w of words) {
    const isLatin = LATIN_REGEX.test(w.word);
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
        const wordsContent = run.words.map((w, wIdx) => {
          const isSpoken = currentTime >= w.start && currentTime <= w.end;
          const wordStartFrame = Math.round(w.start * fps);

          const springProgress = spring({
            fps,
            frame: Math.max(0, (frame - wordStartFrame) * spd),
            config: { stiffness: 220, damping: 11, mass: 0.7 },
          });

          const activeScale = interpolate(springProgress, [0, 0.4, 0.8, 1], [1.0, 1.35, 1.08, 1.12]);
          const scale = isSpoken ? activeScale : 1.0;
          const color = isSpoken ? highlightColor : primaryColor;

          const textStroke = `${outlineWidth}px ${outlineColor}`;
          const textShadow = `
            -${outlineWidth}px -${outlineWidth}px 0 ${outlineColor},
             ${outlineWidth}px -${outlineWidth}px 0 ${outlineColor},
            -${outlineWidth}px  ${outlineWidth}px 0 ${outlineColor},
             ${outlineWidth}px  ${outlineWidth}px 0 ${outlineColor},
             0px 6px 14px rgba(0, 0, 0, 0.85)
          `;

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

        return <React.Fragment key={rIdx}>{wordsContent}</React.Fragment>;
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
        return <React.Fragment key={rIdx}>{wordsContent}</React.Fragment>;
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
        return <React.Fragment key={rIdx}>{wordsContent}</React.Fragment>;
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
        return <React.Fragment key={rIdx}>{wordsContent}</React.Fragment>;
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
        return <React.Fragment key={rIdx}>{wordsContent}</React.Fragment>;
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
            config: { stiffness: 120, damping: 18, mass: 1.0 },
          });

          const opacity = isSpoken ? interpolate(springProgress, [0, 1], [0.35, 1.0]) : 0.7;
          const color = isSpoken ? highlightColor : primaryColor;

          return (
            <span
              key={wIdx}
              style={{
                display: "inline-block",
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
        return <React.Fragment key={rIdx}>{wordsContent}</React.Fragment>;
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
        return <React.Fragment key={rIdx}>{wordsContent}</React.Fragment>;
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
};

export const DEFAULT_TEMPLATE_ID = "hormozi-pop";

export function getTemplateComponent(templateId?: string): React.FC<TemplateProps> {
  const cleanId = (templateId || "").trim().toLowerCase();
  return TEMPLATE_REGISTRY[cleanId] || TEMPLATE_REGISTRY[DEFAULT_TEMPLATE_ID];
}
