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

export const SubtitlesComposition: React.FC<SubtitlesProps> = ({
  words = [],
  primaryColor = "#FFFFFF",
  highlightColor = "#FFE600",
  backgroundColor = "#00FF00", // Green screen default
  wordsPerChunk = 3,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const currentTime = frame / fps;

  // Group words into chunks
  const chunks: WordData[][] = [];
  for (let i = 0; i < words.length; i += wordsPerChunk) {
    chunks.push(words.slice(i, i + wordsPerChunk));
  }

  // Find active chunk
  const activeChunk = chunks.find((chunk) => {
    if (!chunk.length) return false;
    const start = chunk[0].start;
    const end = chunk[chunk.length - 1].end;
    return currentTime >= start && currentTime <= end + 0.2;
  });

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
            const hasBeenSpoken = currentTime > w.end;

            // Pop scale animation on active word
            const popSpring = spring({
              fps,
              frame: Math.max(0, frame - Math.round(w.start * fps)),
              config: { damping: 12, mass: 0.5 },
            });

            const scale = isSpoken ? interpolate(popSpring, [0, 1], [1.0, 1.18]) : 1.0;
            const color = isSpoken ? highlightColor : primaryColor;

            const isLatin = /[a-zA-Z]/.test(w.word);
            return (
              <span
                key={idx}
                dir={isLatin ? "ltr" : undefined}
                style={{
                  fontSize: "64px",
                  fontWeight: 900,
                  color: color,
                  transform: `scale(${scale})`,
                  textShadow:
                    "3px 3px 0 #000, -3px -3px 0 #000, 3px -3px 0 #000, -3px 3px 0 #000, 0px 4px 12px rgba(0,0,0,0.8)",
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
