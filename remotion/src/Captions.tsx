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
const ARABIC_PREFIX_ARTICLE_REGEX = /^(?:[\u0648\u0641\u0628\u0643]?[\u0622\u0623\u0625\u0627]?\u0644[\u0640\-]*|[\u0648\u0641\u0628]?\u0644\u0644[\u0640\-]*|[\u0648\u0641\u0628]?\u0644[\u0640\-]+|[\u0648]?\u0644\u0627[\u0640\-]*|[\u0648]?\u0644\u0648[\u0640\-]*|[\u0648]?\u0644\u064a[\u0640\-]*|[\u0648]?\u0627\u0644\u0644\u064a[\u0640\-]*|[\u0648]?\u062f\u064a[\u0640\-]*|[\u0648]?\u062f\u0648[\u0640\-]*|[\u0648]?\u062f[\u0640\-]+|[\u0648]?[\u0628\u0641\u0643][\u0640\-]+|[\u0648]?[\u064a\u062a\u0646][\u0640\-]+|[\u0648]?\u0645\u0627[\u0640\-]*|[\u0648]?\u064a\u0627[\u0640\-]*|[\u0648]?\u0647\u0627[\u0640\-]*|[\u0628\u0641]?\u0647\u0627\u062f[\u0640\-]*)$/;

function isPrefixToken(token: string, nextToken?: string): boolean {
  const clean = token.replace(/^[^\w\u0600-\u06FF]+|[^\w\u0600-\u06FF]+$/g, "").trim();
  if (!clean) return false;
  if (ARABIC_PREFIX_ARTICLE_REGEX.test(clean) || token.trim().endsWith("-") || token.trim().endsWith("ـ")) {
    return true;
  }
  if (["ي", "ت", "ن"].includes(clean) && nextToken && LATIN_REGEX.test(nextToken)) {
    return true;
  }
  return false;
}

function classifyTokenScript(token: string, fallback: "arabic" | "latin" = "arabic"): "arabic" | "latin" {
  const hasLatin = LATIN_REGEX.test(token);
  const hasArabic = ARABIC_REGEX.test(token);
  if (hasLatin) return "latin";
  if (hasArabic) return "arabic";
  return fallback;
}


export function splitFusedScriptTokens(words: WordToken[]): WordToken[] {
  if (!words || words.length === 0) return [];
  const result: WordToken[] = [];
  const latinThenArabic = /^([a-zA-Z0-9_\-]+)([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF].*)$/;
  const arabicThenLatin = /^([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+[^\w\s\u0640\-]*)([a-zA-Z].*)$/;

  for (const w of words) {
    const text = (w.word || "").trim();
    const dur = Math.max(0.1, (w.end ?? (w.start + 0.3)) - w.start);

    const m1 = text.match(latinThenArabic);
    if (m1 && !text.endsWith("-") && !text.endsWith("ـ")) {
      const p1 = m1[1];
      const p2 = m1[2];
      const mid = Number((w.start + (p1.length / Math.max(1, p1.length + p2.length)) * dur).toFixed(2));
      result.push({ word: p1, start: w.start, end: mid });
      result.push({ word: p2, start: mid, end: w.end });
      continue;
    }

    const m2 = text.match(arabicThenLatin);
    if (m2 && !m2[1].endsWith("-") && !m2[1].endsWith("ـ")) {
      const p1 = m2[1];
      const p2 = m2[2];
      const mid = Number((w.start + (p1.length / Math.max(1, p1.length + p2.length)) * dur).toFixed(2));
      result.push({ word: p1, start: w.start, end: mid });
      result.push({ word: p2, start: mid, end: w.end });
      continue;
    }

    result.push(w);
  }
  return result;
}

const NON_TERMINAL_PARTICLES = new Set([
  "و", "ف", "ب", "ل", "في", "على", "من", "عن", "مع", "إلى", "الى",
  "ما", "لا", "لي", "اللي", "دي", "دو", "يا", "ها", "بهاد", "فهاد", "هاد",
  "la", "le", "les", "un", "une", "des", "du", "de", "d'", "et", "ou",
  "en", "au", "aux", "par", "pour", "avec", "dans", "sur"
]);

function isNonTerminalToken(token: string): boolean {
  const clean = (token || "").replace(/^[^\w\u0600-\u06FF]+|[^\w\u0600-\u06FF]+$/g, "").toLowerCase().trim();
  return NON_TERMINAL_PARTICLES.has(clean) || (token || "").trim().endsWith("-") || (token || "").trim().endsWith("ـ");
}

export function bindArabicArticlesToLatin(words: WordToken[]): WordToken[] {
  if (!words || words.length === 0) return [];
  const bound: WordToken[] = [];
  let i = 0;
  while (i < words.length) {
    const w = words[i];
    const text = (w.word || "").trim();
    const nextWText = i + 1 < words.length ? words[i + 1].word : undefined;
    if (isPrefixToken(text, nextWText) && i + 1 < words.length) {
      const chain = [w];
      let j = i + 1;
      while (j < words.length) {
        const futureWText = j + 1 < words.length ? words[j + 1].word : undefined;
        if (isPrefixToken(words[j].word || "", futureWText)) {
          chain.push(words[j]);
          j++;
        } else {
          break;
        }
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
      return bindArabicArticlesToLatin(splitFusedScriptTokens(transcription.words));
    }
    if (transcription?.segments && transcription.segments.length > 0) {
      const flattened: WordToken[] = [];
      for (const seg of transcription.segments) {
        if (seg.words && seg.words.length > 0) {
          flattened.push(...seg.words);
        }
      }
      return bindArabicArticlesToLatin(splitFusedScriptTokens(flattened));
    }
    return [];
  }, [transcription]);

  // Extract style configuration with fallback defaults
  const fontName = style.font_name || "Cairo";
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

  // Group words into natural speech chunks with strict script separation:
  // Arabic phrases and French loanwords NEVER mix on the same screen chunk.
  const chunks: Array<{ words: WordToken[]; start: number; end: number; script: "arabic" | "latin" }> = React.useMemo(() => {
    if (!allWords || allWords.length === 0) return [];

    // Step 1: Partition into homogeneous script runs and pause blocks
    const runs: Array<{ words: WordToken[]; script: "arabic" | "latin" }> = [];
    let currentRunWords: WordToken[] = [];
    let currentScript: "arabic" | "latin" | null = null;

    for (const w of allWords) {
      const wText = (w.word || "").trim();
      if (!wText) continue;

      const tokenScript = classifyTokenScript(wText, currentScript || "arabic");

      if (currentRunWords.length > 0) {
        const prev = currentRunWords[currentRunWords.length - 1];
        const prevEnd = prev.end ?? prev.start + 0.3;
        const pauseGap = w.start - prevEnd;

        if (tokenScript !== currentScript || pauseGap > 0.8) {
          runs.push({ words: currentRunWords, script: currentScript! });
          currentRunWords = [];
          currentScript = tokenScript;
        }
      }

      if (currentRunWords.length === 0) {
        currentScript = tokenScript;
      }

      currentRunWords.push(w);
    }

    if (currentRunWords.length > 0 && currentScript) {
      runs.push({ words: currentRunWords, script: currentScript });
    }

    // Step 2: Balance sub-chunks per run (strict 2 to 4 words limit)
    const result: Array<{ words: WordToken[]; start: number; end: number; script: "arabic" | "latin" }> = [];

    for (const run of runs) {
      const { words: runWords, script } = run;
      if (runWords.length <= wordsPerLine) {
        result.push({
          words: runWords,
          start: runWords[0].start,
          end: runWords[runWords.length - 1].end ?? (runWords[runWords.length - 1].start + 0.3),
          script,
        });
        continue;
      }

      const sizes = balanceChunkSizes(runWords.length, wordsPerLine);
      let idx = 0;
      const subChunks: WordToken[][] = [];
      for (const sz of sizes) {
        subChunks.push(runWords.slice(idx, idx + sz));
        idx += sz;
      }

      // Grammatical cohesion pass within the run
      for (let cI = 0; cI < subChunks.length - 1; cI++) {
        const currC = subChunks[cI];
        const nextC = subChunks[cI + 1];
        if (currC.length > 0 && isNonTerminalToken(currC[currC.length - 1].word)) {
          if (currC.length > 2) {
            const moved = currC.pop()!;
            nextC.unshift(moved);
          } else if (currC.length < 4 && nextC.length > 0) {
            const moved = nextC.shift()!;
            currC.push(moved);
          }
        }
      }

      for (const slice of subChunks) {
        if (slice.length > 0) {
          result.push({
            words: slice,
            start: slice[0].start,
            end: slice[slice.length - 1].end ?? (slice[slice.length - 1].start + 0.3),
            script,
          });
        }
      }
    }

    return result;
  }, [allWords, wordsPerLine]);

  // Find currently active chunk with silence detection so text doesn't linger across dead air
  const activeChunkInfo = React.useMemo(() => {
    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i];
      const nextChunkStart = i + 1 < chunks.length ? chunks[i + 1].start : null;
      const naturalEnd = chunk.end;
      const minHold = chunk.start + 0.85;

      let effectiveEnd: number;
      if (nextChunkStart !== null) {
        const gap = nextChunkStart - naturalEnd;
        if (gap > 0.8) {
          // Speech paused; dismiss subtitle cleanly 0.35s after word completes
          effectiveEnd = Math.max(chunk.start + 0.3, naturalEnd + 0.35);
        } else {
          effectiveEnd = Math.min(nextChunkStart - 0.05, Math.max(naturalEnd, minHold));
        }
      } else {
        effectiveEnd = Math.max(naturalEnd, minHold);
      }

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
        const isChunkRtl = activeChunkInfo.script === "arabic";
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
