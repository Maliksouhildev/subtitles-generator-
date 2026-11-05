import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

export interface WordData {
  word: string;
  start: number; // in seconds
  end: number;
}

export interface SubtitlesProps {
  words: WordData[];
  primaryColor?: string;
  highlightColor?: string;
  backgroundColor?: string;
  wordsPerChunk?: number;
}

const ARABIC_REGEX = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;
const LATIN_REGEX = /[a-zA-Z]/;
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

function bindArabicArticlesToLatin(words: WordData[]): WordData[] {
  if (!words || words.length === 0) return [];
  const bound: WordData[] = [];
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

// Group consecutive words into Latin vs Arabic runs to prevent breaking parent container's RTL flex order
function groupScriptRuns(words: WordData[]): Array<{ isLatin: boolean; words: WordData[] }> {
  const runs: Array<{ isLatin: boolean; words: WordData[] }> = [];
  let currentRun: WordData[] = [];
  let currentIsLatin: boolean | null = null;
  for (const w of words) {
    const hasLatin = LATIN_REGEX.test(w.word);
    const hasArabic = ARABIC_REGEX.test(w.word);
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

export const SubtitlesComposition: React.FC<SubtitlesProps> = ({
  words = [],
  primaryColor = "#FFFFFF",
  highlightColor = "#FFE600",
  backgroundColor = "#00FF00", // Green screen default
  wordsPerChunk = 3,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const boundWords = React.useMemo(() => bindArabicArticlesToLatin(words), [words]);

  // Natural bilingual speech chunking: 2 to 4 words per chunk
  const chunks: Array<{ words: WordData[]; start: number; end: number; script: "arabic" | "latin" }> = React.useMemo(() => {
    if (!boundWords.length) return [];

    const clauses: WordData[][] = [];
    let currentClause: WordData[] = [];

    for (const w of boundWords) {
      const wText = (w.word || "").trim();
      if (!wText) continue;

      if (currentClause.length > 0) {
        const prev = currentClause[currentClause.length - 1];
        const pauseGap = w.start - prev.end;
        const prevText = (prev.word || "").trim();
        const hasPunct = [",", "،", ".", "!", "?", "؛", ":"].some(p => prevText.endsWith(p));

        if (pauseGap > 0.65 || hasPunct) {
          clauses.push(currentClause);
          currentClause = [];
        }
      }

      currentClause.push(w);
    }

    if (currentClause.length > 0) {
      clauses.push(currentClause);
    }

    const res: Array<{ words: WordData[]; start: number; end: number; script: "arabic" | "latin" }> = [];
    for (const clause of clauses) {
      if (!clause || clause.length === 0) continue;

      const hasArabic = clause.some(w => ARABIC_REGEX.test(w.word || ""));
      const script: "arabic" | "latin" = hasArabic ? "arabic" : "latin";

      if (clause.length <= wordsPerChunk) {
        res.push({
          words: clause,
          start: clause[0].start,
          end: clause[clause.length - 1].end,
          script
        });
        continue;
      }

      const sizes = balanceChunkSizes(clause.length, wordsPerChunk);
      let idx = 0;
      for (const sz of sizes) {
        const slice = clause.slice(idx, idx + sz);
        if (slice.length > 0) {
          res.push({
            words: slice,
            start: slice[0].start,
            end: slice[slice.length - 1].end,
            script
          });
        }
        idx += sz;
      }
    }
    return res;
  }, [boundWords, wordsPerChunk]);

  // Find active chunk with silence gap cutoff (>0.65s silence dismisses subtitle) & max 2.5s duration
  const activeChunk = React.useMemo(() => {
    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i];
      const nextChunkStart = i + 1 < chunks.length ? chunks[i + 1].start : null;
      const naturalEnd = chunk.end;
      const minHold = chunk.start + 0.85;

      let effectiveEnd: number;
      if (nextChunkStart !== null) {
        const gap = nextChunkStart - naturalEnd;
        if (gap > 0.65) {
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

  const strokeWidth = 3.5;
  const textShadow = `
    -${strokeWidth}px -${strokeWidth}px 0 #000,
     ${strokeWidth}px -${strokeWidth}px 0 #000,
    -${strokeWidth}px  ${strokeWidth}px 0 #000,
     ${strokeWidth}px  ${strokeWidth}px 0 #000,
     0px 3px 6px rgba(0, 0, 0, 0.65)
  `;

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        backgroundColor: backgroundColor,
        display: "flex",
        alignItems: "center",
        justifyContent: "flex-end",
        flexDirection: "column",
        paddingBottom: "180px",
        fontFamily: "'Cairo', 'Tajawal', sans-serif",
        direction: activeChunk?.script === "latin" ? "ltr" : "rtl",
      }}
    >
      {activeChunk && (() => {
        const runs = groupScriptRuns(activeChunk.words);
        return (
          <div
            dir="rtl"
            style={{
              display: "flex",
              direction: activeChunk?.script === "latin" ? "ltr" : "rtl",
              gap: "14px",
              justifyContent: "center",
              alignItems: "center",
              flexWrap: "wrap",
              padding: "0 40px",
            }}
          >
            {runs.map((run, rIdx) => {
              const runContent = run.words.map((w, wIdx) => {
                const isSpoken = currentTime >= w.start && currentTime <= w.end;
                const wordStartFrame = Math.round(w.start * fps);
                const wordEndFrame = Math.round(w.end * fps);

                // Remotion spring pop mapped to CSS scale for viral Hormozi look
                const popSpring = spring({
                  fps,
                  frame: Math.max(0, frame - wordStartFrame),
                  config: { damping: 10, mass: 0.4, stiffness: 220 },
                });

                const decaySpring = spring({
                  fps,
                  frame: Math.max(0, frame - wordEndFrame),
                  config: { damping: 14, mass: 0.45, stiffness: 190 },
                });

                // Physically pop up to 1.28 on impact -> settles at 1.15
                const popScale = interpolate(
                  popSpring,
                  [0, 0.4, 0.75, 1.0],
                  [1.0, 1.28, 1.12, 1.15],
                  { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
                );

                const decayScale = interpolate(decaySpring, [0, 1], [1.15, 1.0], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                });

                let scale = 1.0;
                if (isSpoken) {
                  scale = popScale;
                } else if (currentTime > w.end && frame - wordEndFrame < 10) {
                  scale = decayScale;
                }

                const color = isSpoken ? highlightColor : primaryColor;

                return (
                  <span
                    key={`w-${rIdx}-${wIdx}`}
                    style={{
                      fontSize: "64px",
                      fontWeight: 900,
                      color: color,
                      transform: `scale(${scale})`,
                      transformOrigin: "center bottom",
                      textShadow,
                      WebkitTextStroke: `${strokeWidth}px #000`,
                      paintOrder: "stroke fill",
                      display: "inline-block",
                      lineHeight: 1.15,
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
                    key={`run-${rIdx}`}
                    dir="ltr"
                    style={{
                      display: "inline-flex",
                      direction: "ltr",
                      unicodeBidi: "isolate",
                      alignItems: "center",
                      gap: "10px",
                      margin: "0 4px",
                    }}
                  >
                    {runContent}
                  </span>
                );
              }

              return (
                <span
                  key={`run-${rIdx}`}
                  dir="rtl"
                  style={{
                    display: "inline-flex",
                    direction: activeChunk?.script === "latin" ? "ltr" : "rtl",
                    unicodeBidi: "isolate",
                    alignItems: "center",
                    gap: "10px",
                    margin: "0 4px",
                  }}
                >
                  {runContent}
                </span>
              );
            })}
          </div>
        );
      })()}
    </div>
  );
};
