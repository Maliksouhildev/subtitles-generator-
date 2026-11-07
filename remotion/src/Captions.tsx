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
  "بهذا", "هذا", "هادي", "يعني", "كيما", "باش", "باشما", "علاش", "كيفاش", "وين", "وقتاش",
  "بلي", "كي", "غير", "حتى", "ما كاين", "ماكاين", "ما كاش", "ماكاش", "ما كانش",
  "la", "le", "les", "un", "une", "des", "du", "de", "d'", "et", "ou",
  "en", "au", "aux", "par", "pour", "avec", "dans", "sur"
]);

function isNonTerminalToken(token: string): boolean {
  const clean = (token || "").replace(/^[^\w\u0600-\u06FF]+|[^\w\u0600-\u06FF]+$/g, "").toLowerCase().trim();
  if (NON_TERMINAL_PARTICLES.has(clean) || (token || "").trim().endsWith("-") || (token || "").trim().endsWith("ـ")) {
    return true;
  }
  if ((clean.startsWith("و") || clean.startsWith("ف")) && clean.length > 1 && NON_TERMINAL_PARTICLES.has(clean.slice(1))) {
    return true;
  }
  return false;
}



export function bindArabicArticlesToLatin(words: WordToken[]): WordToken[] {

  if (!words || words.length === 0) return [];
  // Restore dropped definite articles: 'وكان شرف' -> 'وكان الشرف'
  for (let idx = 0; idx < words.length - 1; idx++) {
    const w1 = (words[idx].word || "").trim();
    const w2 = (words[idx + 1].word || "").trim();
    if (["وكان", "كان"].includes(w1) && w2 === "شرف") {
      words[idx + 1].word = "الشرف";
    }
  }

  const bound: WordToken[] = [];

  let i = 0;

  while (i < words.length) {

    const w = words[i];

    const text = (w.word || "").trim();



    // Merge isolated punctuation into previous word

    if ([",", "،", ".", "!", "?", "؛", ":"].includes(text) && bound.length > 0) {

      const prev = bound[bound.length - 1];

      prev.word = `${prev.word}${text}`;

      prev.end = Math.max(prev.end ?? 0, w.end ?? 0);

      i += 1;

      continue;

    }



    const nextW = i + 1 < words.length ? words[i + 1] : undefined;

    const nextWText = nextW ? (nextW.word || "").trim() : undefined;



    // Bind French loan expressions: "par" + "rapport", "c'est" + "bon"

    if (text.toLowerCase() === "par" && nextWText && nextWText.toLowerCase().startsWith("rapport")) {

      bound.push({

        word: `${text} ${nextWText}`,

        start: w.start,

        end: nextW!.end ?? (nextW!.start + 0.3),

      });

      i += 2;

      continue;

    }

    if (["c'est", "سي"].includes(text.toLowerCase()) && nextWText && (nextWText.toLowerCase().startsWith("bon") || nextWText.startsWith("بون"))) {

      bound.push({

        word: `${text} ${nextWText}`,

        start: w.start,

        end: nextW!.end ?? (nextW!.start + 0.3),

      });

      i += 2;

      continue;

    }



    // Bind French article to Latin loanword: "le" + "premier", "la" + "nouvelle"

    const cleanTv = text.replace(/^[^\w]+|[^\w]+$/g, "").toLowerCase();

    if (["la", "le", "les", "un", "une", "des", "du"].includes(cleanTv) && nextWText && LATIN_REGEX.test(nextWText)) {

      bound.push({

        word: `${text} ${nextWText}`,

        start: w.start,

        end: nextW!.end ?? (nextW!.start + 0.3),

      });

      i += 2;

      continue;

    }



    // Arabic-only prefixes (e.g. 'و' + 'السيارة') - never across to Latin!

    if (isPrefixToken(text, nextWText) && i + 1 < words.length && !LATIN_REGEX.test(nextWText || "")) {

      const chain = [w];

      let j = i + 1;

      while (j < words.length) {

        const futureWText = j + 1 < words.length ? words[j + 1].word : undefined;

        if (isPrefixToken(words[j].word || "", futureWText) && !LATIN_REGEX.test(futureWText || "")) {

          chain.push(words[j]);

          j++;

        } else {

          break;

        }

      }

      if (j < words.length && !LATIN_REGEX.test(words[j].word || "")) {

        const targetWord = words[j];

        const jointText = chain.map((item) => (item.word || "").trim()).join(" ") + " " + (targetWord.word || "").trim();

        bound.push({

          word: jointText.trim(),

          start: chain[0].start,

          end: targetWord.end ?? (targetWord.start + 0.3),

        });

        i = j + 1;

        continue;

      } else if (!LATIN_REGEX.test(words[i + 1].word || "")) {

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

  const effectiveTarget = Math.min(6, Math.max(3, targetSize || 5));

  if (totalWords <= effectiveTarget + 1 && totalWords <= 6) return [totalWords];

  let numChunks = Math.max(1, Math.ceil(totalWords / effectiveTarget));

  let baseSize = Math.floor(totalWords / numChunks);

  let remainder = totalWords % numChunks;

  let sizes = Array.from({ length: numChunks }, (_, k) => baseSize + (k < remainder ? 1 : 0));

  while (sizes.some(s => s > 6)) {

    numChunks++;

    baseSize = Math.floor(totalWords / numChunks);

    remainder = totalWords % numChunks;

    sizes = Array.from({ length: numChunks }, (_, k) => baseSize + (k < remainder ? 1 : 0));

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

  const wordsPerLine = Math.min(6, Math.max(3, style.words_per_line ?? 5));

  const subBoxStyle = style.sub_box_style || "none";

  const subBoxColor = style.sub_box_color || "#000000";

  const subBoxAlpha = style.sub_box_alpha ?? 0.85;



  // Group words into single-line bilingual speech chunks with strict French/Arabic script isolation:

  const chunks: Array<{ words: WordToken[]; start: number; end: number; script: "arabic" | "latin" }> = React.useMemo(() => {

    if (!allWords || allWords.length === 0) return [];



    const effectiveTarget = Math.min(4, Math.max(2, wordsPerLine || 4));



    const rawChunks: Array<{ words: WordToken[]; script: "arabic" | "latin" }> = [];

    let curChunk: WordToken[] = [];

    let curScript: "arabic" | "latin" | null = null;



    for (const w of allWords) {

      const wText = (w.word || "").trim();

      if (!wText) continue;



      const wScript: "arabic" | "latin" = LATIN_REGEX.test(wText) ? "latin" : "arabic";



      let pauseGap = 0;

      if (curChunk.length > 0) {

        const prevEnd = curChunk[curChunk.length - 1].end ?? (curChunk[curChunk.length - 1].start + 0.3);

        pauseGap = w.start - prevEnd;

      }



      const prevText = curChunk.length > 0 ? (curChunk[curChunk.length - 1].word || "").trim() : "";
      const prevClean = prevText.replace(/^[^\w\u0600-\u06FF]+|[^\w\u0600-\u06FF]+$/g, "").toLowerCase().trim();
      const hasMajorStop = [".", "!", "?", "،", ","].some((p) => prevText.endsWith(p));

      const isInseparable = (["ما كاين", "ماكاين", "ما كاش", "ماكاش", "ما كانش"].includes(prevClean) && wText.startsWith("حتى")) || (prevClean === "حتى" && !isNonTerminalToken(wText));

      let shouldBreak = false;
      if (curChunk.length > 0) {
        // Forced break before and after Latin loan strings to eliminate BiDi layout collisions
        if (wScript !== curScript) {
          shouldBreak = true;
        } else if (pauseGap > 0.50) {
          shouldBreak = true;
        } else if (isInseparable) {
          shouldBreak = false;
        } else if (curChunk.length >= effectiveTarget) {
          shouldBreak = true;
        } else if (curChunk.length >= 2 && isNonTerminalToken(wText)) {
          shouldBreak = true;
        } else if (hasMajorStop && curChunk.length >= 2) {
          shouldBreak = true;
        }
      }

      }



      if (shouldBreak && curChunk.length > 0 && curScript) {

        rawChunks.push({ words: curChunk, script: curScript });

        curChunk = [];

      }



      curChunk.push(w);

      curScript = wScript;

    }



    if (curChunk.length > 0 && curScript) {

      rawChunks.push({ words: curChunk, script: curScript });

    }



    // Merge tiny 1-word fragment ONLY if same script, no pause (<= 0.4s), and won't exceed 4 words

    const result: Array<{ words: WordToken[]; start: number; end: number; script: "arabic" | "latin" }> = [];

    for (const rc of rawChunks) {

      if (!rc.words || rc.words.length === 0) continue;

      if (result.length > 0) {

        const prev = result[result.length - 1];

        const prevEnd = prev.words[prev.words.length - 1].end ?? (prev.words[prev.words.length - 1].start + 0.3);

        const gap = rc.words[0].start - prevEnd;

        if (prev.script === rc.script && gap <= 0.40 && prev.words.length + rc.words.length <= effectiveTarget && (rc.words.length === 1 || prev.words.length === 1)) {

          prev.words.push(...rc.words);

          prev.end = rc.words[rc.words.length - 1].end ?? (rc.words[rc.words.length - 1].start + 0.3);

          continue;

        }

      }



      result.push({

        words: rc.words,

        start: rc.words[0].start,

        end: rc.words[rc.words.length - 1].end ?? (rc.words[rc.words.length - 1].start + 0.3),

        script: rc.script,

      });

    }



    return result;

  }, [allWords, wordsPerLine]);



  // Find currently active chunk with silence detection & max duration rule (<= 2.5s)

  const activeChunkInfo = React.useMemo(() => {

    for (let i = 0; i < chunks.length; i++) {

      const chunk = chunks[i];

      const nextChunkStart = i + 1 < chunks.length ? chunks[i + 1].start : null;

      const naturalEnd = chunk.end;

      const minHold = chunk.start + 0.85;



      let effectiveEnd: number;

      if (nextChunkStart !== null) {

        const gap = nextChunkStart - naturalEnd;

        if (gap > 0.50) {

          effectiveEnd = Math.max(chunk.start + 0.3, naturalEnd + 0.35);

        } else {

          effectiveEnd = Math.min(nextChunkStart - 0.05, Math.max(naturalEnd, minHold));

        }

      } else {

        effectiveEnd = Math.max(naturalEnd, minHold);

      }



      effectiveEnd = Math.min(chunk.start + 2.5, Math.max(chunk.start + 0.25, effectiveEnd));



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

