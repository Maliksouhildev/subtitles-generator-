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

const ARABIC_PREFIX_ARTICLE_REGEX = /^(?:و?الـ?|و?ال-|و?ال|لـ?|ل-|للـ?|لل-|فـ?|ف-|بـ?|ب-|لا)$/;
const LATIN_REGEX = /[a-zA-Z]/;

function bindArabicArticlesToLatin(words: WordData[]): WordData[] {
  if (!words || words.length === 0) return [];
  const bound: WordData[] = [];
  let i = 0;
  while (i < words.length) {
    const w = words[i];
    const text = (w.word || "").trim();
    if (ARABIC_PREFIX_ARTICLE_REGEX.test(text) && i + 1 < words.length) {
      const nextW = words[i + 1];
      const nextText = (nextW.word || "").trim();
      if (LATIN_REGEX.test(nextText)) {
        bound.push({
          word: `${text} ${nextText}`,
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

  // Group words into chunks
  const chunks: WordData[][] = [];
  for (let i = 0; i < boundWords.length; i += wordsPerChunk) {
    chunks.push(boundWords.slice(i, i + wordsPerChunk));
  }

  // Find active chunk
  const activeChunk = chunks.find((chunk) => {
    if (!chunk.length) return false;
    const start = chunk[0].start;
    const end = chunk[chunk.length - 1].end;
    return currentTime >= start && currentTime <= end + 0.2;
  });

  const strokeWidth = 8;
  const textShadow = `
    -${strokeWidth}px -${strokeWidth}px 0 #000,
     ${strokeWidth}px -${strokeWidth}px 0 #000,
    -${strokeWidth}px  ${strokeWidth}px 0 #000,
     ${strokeWidth}px  ${strokeWidth}px 0 #000,
     0px 10px 0px #000,
     3px 10px 0px #000,
    -3px 10px 0px #000,
     0px 14px 22px rgba(0, 0, 0, 0.95)
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
        fontFamily: "'Cairo', sans-serif",
        direction: "rtl",
      }}
    >
      {activeChunk && (
        <div
          style={{
            display: "flex",
            gap: "18px",
            justifyContent: "center",
            flexWrap: "wrap",
            padding: "0 40px",
          }}
        >
          {activeChunk.map((w, idx) => {
            const isSpoken = currentTime >= w.start && currentTime <= w.end;
            const wordStartFrame = Math.round(w.start * fps);
            const wordEndFrame = Math.round(w.end * fps);

            // Snappy Remotion spring pop with fast attack
            const popSpring = spring({
              fps,
              frame: Math.max(0, frame - wordStartFrame),
              config: { damping: 11, mass: 0.4, stiffness: 220 },
            });

            const decaySpring = spring({
              fps,
              frame: Math.max(0, frame - wordEndFrame),
              config: { damping: 14, mass: 0.5, stiffness: 180 },
            });

            // 115% scale pop modifier
            const activeScale = interpolate(
              popSpring,
              [0, 0.35, 0.7, 1.0],
              [1.0, 1.25, 1.12, 1.15],
              { extrapolateRight: "clamp" }
            );

            let scale = 1.0;
            if (isSpoken) {
              scale = activeScale;
            } else if (currentTime > w.end && frame - wordEndFrame < 8) {
              scale = interpolate(decaySpring, [0, 1], [1.15, 1.0], { extrapolateRight: "clamp" });
            }

            const color = isSpoken ? highlightColor : primaryColor;
            const isLatin = LATIN_REGEX.test(w.word);

            return (
              <span
                key={idx}
                dir={isLatin ? "ltr" : undefined}
                style={{
                  fontSize: "64px",
                  fontWeight: 900,
                  color: color,
                  transform: `scale(${scale})`,
                  transformOrigin: "center bottom",
                  textShadow,
                  WebkitTextStroke: `${strokeWidth}px #000`,
                  paintOrder: "stroke fill",
                  transition: "color 0.1s ease",
                  display: "inline-block",
                  direction: isLatin ? "ltr" : undefined,
                  unicodeBidi: isLatin ? "isolate" : undefined,
                }}
              >
                {w.word}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
};
