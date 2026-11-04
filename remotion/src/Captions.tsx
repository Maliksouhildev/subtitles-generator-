import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import {
  WordToken,
  CaptionsStyleProps,
  getTemplateComponent,
  DEFAULT_TEMPLATE_ID,
} from "./TemplateMapper";

export type { WordToken, CaptionsStyleProps };

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
  template_id?: string;
  style?: CaptionsStyleProps;
  backgroundMode?: "transparent" | "green_screen" | "black" | "blue" | "custom";
  customColorHex?: string;
}

// Regex to detect French / English loanwords embedded in Arabic text
const LATIN_REGEX = /[a-zA-Z]/;
const ARABIC_REGEX = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;
const ARABIC_PREFIX_ARTICLE_REGEX = /^(?:[\u0648\u0641\u0628\u0643]?[\u0622\u0623\u0625\u0627]?\u0644[\u0640\-]*|[\u0648\u0641\u0628]?\u0644\u0644[\u0640\-]*|[\u0648\u0641\u0628]?\u0644[\u0640\-]+|[\u0648]?\u0644\u0627[\u0640\-]*|[\u0648]?\u0644\u0648[\u0640\-]*|[\u0648]?\u0644\u064a[\u0640\-]*|[\u0648]?\u0627\u0644\u0644\u064a[\u0640\-]*|[\u0648]?\u062f\u064a[\u0640\-]*|[\u0648]?\u062f\u0648[\u0640\-]*|[\u0648]?\u062f[\u0640\-]+|[\u0648]?[\u0628\u0641\u0643][\u0640\-]+|[\u0648]?\u0645\u0627[\u0640\-]*|[\u0648]?\u064a\u0627[\u0640\-]*|[\u0648]?\u0647\u0627[\u0640\-]*|[\u0628\u0641]?\u0647\u0627\u062f[\u0640\-]*)$/;

function isPrefixToken(token: string): boolean {
  const clean = token.replace(/^[^\w\u0600-\u06FF]+|[^\w\u0600-\u06FF]+$/g, "").trim();
  if (!clean) return false;
  return ARABIC_PREFIX_ARTICLE_REGEX.test(clean) || token.trim().endsWith("-") || token.trim().endsWith("ـ");
}

export function bindArabicArticlesToLatin(words: WordToken[]): WordToken[] {
  if (!words || words.length === 0) return [];
  const bound: WordToken[] = [];
  let i = 0;
  while (i < words.length) {
    const w = words[i];
    const text = (w.word || "").trim();
    if (isPrefixToken(text) && i + 1 < words.length) {
      const chain = [w];
      let j = i + 1;
      while (j < words.length && isPrefixToken(words[j].word || "")) {
        chain.push(words[j]);
        j++;
      }
      if (j < words.length) {
        const targetWord = words[j];
        const jointText = chain.map((item) => (item.word || "").trim()).join(" ") + " " + (targetWord.word || "").trim();
        bound.push({
          word: jointText.trim(),
          start: chain[0].start,
          end: targetWord.end ?? (targetWord.start + 0.3),
        });
        i = j + 1;
        continue;
      } else {
        const nextW = words[i + 1];
        bound.push({
          word: `${text} ${(nextW.word || "").trim()}`,
          start: w.start,
          end: nextW.end ?? (nextW.start + 0.3),
        });
        i += 2;
        continue;
      }
    }
    bound.push(w);
    i += 1;
  }
  return bound;
}

// Helper: Anti-orphan balanced chunking enforcing strict 3-to-4 word limit per chunk
function balanceChunkSizes(totalWords: number, targetSize: number): number[] {
  const effectiveTarget = Math.min(4, Math.max(2, targetSize || 3));
  if (totalWords <= effectiveTarget) return [totalWords];
  const numChunks = Math.ceil(totalWords / effectiveTarget);
  if (totalWords % effectiveTarget === 1 && numChunks > 1) {
    const baseSize = Math.floor(totalWords / numChunks);
    const remainder = totalWords % numChunks;
    return Array.from({ length: numChunks }, (_, k) => Math.min(4, baseSize + (k < remainder ? 1 : 0)));
  }
  const sizes: number[] = [];
  let remaining = totalWords;
  while (remaining > 0) {
    if (remaining === effectiveTarget + 1) {
      const half = Math.floor(remaining / 2);
      sizes.push(Math.min(4, remaining - half));
      sizes.push(Math.min(4, half));
      break;
    }
    const take = Math.min(4, Math.min(effectiveTarget, remaining));
    sizes.push(take);
    remaining -= take;
  }
  return sizes;
}

export const Captions: React.FC<CaptionsCompositionProps> = ({
  transcription,
  template_id,
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
      return bindArabicArticlesToLatin(transcription.words);
    }
    if (transcription?.segments && transcription.segments.length > 0) {
      const flattened: WordToken[] = [];
      for (const seg of transcription.segments) {
        if (seg.words && seg.words.length > 0) {
          flattened.push(...seg.words);
        }
      }
      return bindArabicArticlesToLatin(flattened);
    }
    return [];
  }, [transcription]);

  // Extract style configuration with fallback defaults
  const fontName = style.font_name || "Lalezar";
  const fontSize = style.font_size || 58;
  const primaryColor = style.primary_color || "#FFFFFF";
  const highlightColor = style.highlight_color || "#FFE600";
  const outlineColor = style.outline_color || "#000000";
  const outlineWidth = style.outline_width ?? 2.4;
  const marginV = style.margin_v ?? 960;
  const wordsPerLine = Math.min(4, Math.max(2, style.words_per_line ?? 3));
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
      const minHold = chunk.start + 0.85;
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
      {activeChunkInfo && (() => {
        const isChunkRtl = activeChunkInfo.words.some((w) => ARABIC_REGEX.test(w.word));
        const activeTemplateId = template_id || style.animation_style || DEFAULT_TEMPLATE_ID;
        const TemplateComponent = getTemplateComponent(activeTemplateId);

        // Dynamic block entrance animation driven by Remotion spring()
        const chunkStartFrame = Math.round(activeChunkInfo.start * fps);
        const chunkSpring = spring({
          fps,
          frame: Math.max(0, frame - chunkStartFrame),
          config: { damping: 13, mass: 0.45, stiffness: 180 },
        });
        const chunkScale = interpolate(chunkSpring, [0, 1], [0.92, 1.0], {
          extrapolateRight: "clamp",
        });
        const chunkTranslateY = interpolate(chunkSpring, [0, 1], [10, 0], {
          extrapolateRight: "clamp",
        });
        const chunkOpacity = interpolate(chunkSpring, [0, 1], [0.25, 1.0], {
          extrapolateRight: "clamp",
        });

        return (
          <div
            dir={isChunkRtl ? "rtl" : "ltr"}
            style={{
              display: "flex",
              flexDirection: "row",
              flexWrap: "wrap",
              alignItems: "center",
              justifyContent: "center",
              textAlign: "center",
              direction: isChunkRtl ? "rtl" : "ltr",
              unicodeBidi: "isolate",
              transform: `scale(${chunkScale}) translateY(${chunkTranslateY}px)`,
              opacity: chunkOpacity,
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
            <TemplateComponent
              chunk={activeChunkInfo}
              currentTime={currentTime}
              frame={frame}
              fps={fps}
              style={style}
              isChunkRtl={isChunkRtl}
            />
          </div>
        );
      })()}
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
