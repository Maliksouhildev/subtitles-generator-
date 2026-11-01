import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

export interface WordToken {
  word: string;
  start: number; // in seconds
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
  margin_v?: number; // Distance in pixels from bottom (out of 1920)
  words_per_line?: number;
  animation_style?: string;
  sub_box_style?: "none" | "pill" | "box" | "shadow";
  sub_box_color?: string;
  sub_box_alpha?: number;
}

export interface CaptionsCompositionProps {
  transcription: {
    text?: string;
    segments?: Array<{
      start: number;
      end: number;
      text: string;
      words: WordToken[];
    }>;
    words?: WordToken[];
  };
  style?: CaptionsStyleProps;
  backgroundMode?: "transparent" | "green_screen" | "black" | "blue" | "custom";
  customColorHex?: string;
}

// Regex to detect French / English loanwords embedded in Arabic text
const LATIN_REGEX = /[a-zA-Z]/;

// Helper: Anti-orphan balanced chunking so fast audio never flashes 1 isolated word
function balanceChunkSizes(totalWords: number, targetSize: number): number[] {
  if (totalWords <= targetSize) return [totalWords];
  const numChunks = Math.ceil(totalWords / targetSize);
  if (totalWords % targetSize === 1 && numChunks > 1) {
    const baseSize = Math.floor(totalWords / numChunks);
    const remainder = totalWords % numChunks;
    return Array.from({ length: numChunks }, (_, k) => baseSize + (k < remainder ? 1 : 0));
  }
  const sizes: number[] = [];
  let remaining = totalWords;
  while (remaining > 0) {
    if (remaining === targetSize + 1) {
      const half = Math.floor(remaining / 2);
      sizes.push(remaining - half);
      sizes.push(half);
      break;
    }
    const take = Math.min(targetSize, remaining);
    sizes.push(take);
    remaining -= take;
  }
  return sizes;
}

export const Captions: React.FC<CaptionsCompositionProps> = ({
  transcription,
  style = {},
  backgroundMode = "transparent",
  customColorHex = "#1a1a24",
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const currentTime = frame / fps;

  // Extract flat list of all word tokens with valid timestamps
  const allWords: WordToken[] = React.useMemo(() => {
    if (transcription?.words && transcription.words.length > 0) {
      return transcription.words;
    }
    if (transcription?.segments && transcription.segments.length > 0) {
      const flattened: WordToken[] = [];
      for (const seg of transcription.segments) {
        if (seg.words && seg.words.length > 0) {
          flattened.push(...seg.words);
        }
      }
      return flattened;
    }
    return [];
  }, [transcription]);

  // Extract style configuration with fallback defaults
  const fontName = style.font_name || "Lalezar";
  const fontSize = style.font_size || 58;
  const primaryColor = style.primary_color || "#FFFFFF";
  const highlightColor = style.highlight_color || "#FFE600";
  const outlineColor = style.outline_color || "#000000";
  const outlineWidth = style.outline_width ?? 3.5;
  const marginV = style.margin_v ?? 420;
  const wordsPerLine = style.words_per_line ?? 3;
  const subBoxStyle = style.sub_box_style || "none";
  const subBoxColor = style.sub_box_color || "#000000";
  const subBoxAlpha = style.sub_box_alpha ?? 0.85;

  // Group words into natural speech chunks with balanced sizes
  const chunks: Array<{ words: WordToken[]; start: number; end: number }> = React.useMemo(() => {
    if (!allWords || allWords.length === 0) return [];

    // Group into pause blocks (pauses > 0.9s break line)
    const pauseBlocks: WordToken[][] = [];
    let currentBlock: WordToken[] = [];

    for (const w of allWords) {
      if (currentBlock.length > 0) {
        const prev = currentBlock[currentBlock.length - 1];
        if (w.start - prev.end > 0.9) {
          pauseBlocks.push(currentBlock);
          currentBlock = [];
        }
      }
      currentBlock.push(w);
    }
    if (currentBlock.length > 0) pauseBlocks.push(currentBlock);

    // Apply balanced chunking per pause block
    const result: Array<{ words: WordToken[]; start: number; end: number }> = [];
    for (const block of pauseBlocks) {
      const sizes = balanceChunkSizes(block.length, wordsPerLine);
      let idx = 0;
      for (const sz of sizes) {
        const slice = block.slice(idx, idx + sz);
        if (slice.length > 0) {
          result.push({
            words: slice,
            start: slice[0].start,
            end: slice[slice.length - 1].end,
          });
        }
        idx += sz;
      }
    }
    return result;
  }, [allWords, wordsPerLine]);

  // Find currently active chunk with minimum hold duration so phrase never flickers out
  const activeChunkInfo = React.useMemo(() => {
    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i];
      const nextChunkStart = i + 1 < chunks.length ? chunks[i + 1].start : null;
      const naturalEnd = chunk.end;
      const minHold = chunk.start + 0.65;
      const effectiveEnd = nextChunkStart
        ? Math.min(nextChunkStart - 0.05, Math.max(naturalEnd, minHold))
        : Math.max(naturalEnd, minHold);

      if (currentTime >= chunk.start && currentTime <= effectiveEnd) {
        return chunk;
      }
    }
    return null;
  }, [chunks, currentTime]);

  // Background style calculation
  const getBackgroundColor = () => {
    switch (backgroundMode) {
      case "green_screen":
        return "#00FF00";
      case "black":
        return "#000000";
      case "blue":
        return "#0000FF";
      case "custom":
        return customColorHex;
      case "transparent":
      default:
        return "transparent";
    }
  };

  // Convert bottom vertical margin (assumes 1920 reference height) to responsive bottom style
  const bottomDistance = `${(marginV / 1920) * 100}%`;

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        backgroundColor: getBackgroundColor(),
        position: "relative",
        overflow: "hidden",
        display: "flex",
        alignItems: "center",
        justifyContent: "flex-end",
        flexDirection: "column",
        paddingBottom: bottomDistance,
        boxSizing: "border-box",
        fontFamily: `'${fontName}', 'Cairo', 'Almarai', sans-serif`,
      }}
    >
      {activeChunkInfo && (
        <div
          dir="rtl"
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            flexWrap: "nowrap",
            direction: "rtl",
            unicodeBidi: "isolate",
            gap: "14px",
            padding: subBoxStyle === "pill"
              ? "10px 28px"
              : subBoxStyle === "box"
              ? "12px 24px"
              : "6px 12px",
            backgroundColor:
              subBoxStyle !== "none"
                ? hexToRgba(subBoxColor, subBoxAlpha)
                : "transparent",
            borderRadius:
              subBoxStyle === "pill"
                ? "9999px"
                : subBoxStyle === "box"
                ? "14px"
                : "0",
            border:
              subBoxStyle !== "none"
                ? `3.5px solid ${outlineColor}`
                : "none",
            boxShadow:
              subBoxStyle === "shadow"
                ? "0 10px 30px rgba(0,0,0,0.85)"
                : subBoxStyle !== "none"
                ? "0 6px 16px rgba(0,0,0,0.6)"
                : "none",
            maxWidth: "92%",
          }}
        >
          {activeChunkInfo.words.map((w, idx) => {
            const isSpoken = currentTime >= w.start && currentTime <= w.end;
            const isLatin = LATIN_REGEX.test(w.word);

            // Remotion Spring Physics (stiffness: 180, damping: 10, mass: 0.8)
            const wordStartFrame = Math.round(w.start * fps);
            const springProgress = spring({
              fps,
              frame: Math.max(0, frame - wordStartFrame),
              config: { stiffness: 180, damping: 10, mass: 0.8 },
            });

            // Scale progression: Overshoot 1.30 -> Recoil -> Resting 1.10
            const activeScale = interpolate(springProgress, [0, 0.4, 0.8, 1], [1.0, 1.30, 1.07, 1.12]);
            const scale = isSpoken ? activeScale : 1.0;
            const color = isSpoken ? highlightColor : primaryColor;

            const textStroke = `${outlineWidth}px ${outlineColor}`;
            const textShadow = `
              -${outlineWidth}px -${outlineWidth}px 0 ${outlineColor},
               ${outlineWidth}px -${outlineWidth}px 0 ${outlineColor},
              -${outlineWidth}px  ${outlineWidth}px 0 ${outlineColor},
               ${outlineWidth}px  ${outlineWidth}px 0 ${outlineColor},
               0px 4px 10px rgba(0, 0, 0, 0.75)
            `;

            return (
              <span
                key={idx}
                style={{
                  display: "inline-block",
                  transform: `scale(${scale})`,
                  transformOrigin: "center bottom",
                  color,
                  fontSize: `${fontSize}px`,
                  fontWeight: 900,
                  textShadow,
                  WebkitTextStroke: textStroke,
                  letterSpacing: isLatin ? "1px" : "0.5px",
                  lineHeight: 1.15,
                  transition: "color 0.08s ease",
                  userSelect: "none",
                  whiteSpace: "nowrap",
                }}
              >
                {isLatin ? (
                  /* BiDi Isolation Container: Prevents French/English loanwords from jumbling adjacent Arabic */
                  <span
                    dir="ltr"
                    style={{
                      display: "inline-block",
                      direction: "ltr",
                      unicodeBidi: "isolate",
                      margin: "0 4px",
                    }}
                  >
                    {w.word}
                  </span>
                ) : (
                  w.word
                )}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
};

// Helper: Hex to RGBA
function hexToRgba(hex: string, alpha: number): string {
  const clean = hex.replace("#", "");
  const r = parseInt(clean.substring(0, 2), 16) || 0;
  const g = parseInt(clean.substring(2, 4), 16) || 0;
  const b = parseInt(clean.substring(4, 6), 16) || 0;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
