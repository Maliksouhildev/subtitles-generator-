import React from "react";
import { Composition } from "remotion";
import { Captions, CaptionsCompositionProps } from "./Captions";

// Default realistic sample for previewing Algerian Darija with French loanwords
const defaultSampleProps: CaptionsCompositionProps = {
  transcription: {
    words: [
      { word: "le premier", start: 0.1, end: 0.7 },
      { word: "test", start: 0.75, end: 1.1 },
      { word: "بهذا", start: 1.15, end: 1.5 },
      { word: "la nouvelle", start: 1.55, end: 2.1 },
      { word: "وكان", start: 2.2, end: 2.6 },
      { word: "شرف", start: 2.65, end: 3.0 },
      { word: "للشركة", start: 3.05, end: 3.6 },
      { word: "ما", start: 3.9, end: 4.2 },
      { word: "كاين", start: 4.25, end: 4.6 },
      { word: "حتى", start: 4.65, end: 5.0 },
      { word: "إشكال", start: 5.05, end: 5.5 },
      { word: "على", start: 5.55, end: 5.85 },
      { word: "الهيكل", start: 5.9, end: 6.4 },
    ],
  },
  template_id: "hormozi-pop",
  style: {
    font_name: "Cairo",
    font_size: 62,
    primary_color: "#FFFFFF",
    highlight_color: "#FFE600",
    outline_color: "#000000",
    outline_width: 3.5,
    margin_v: 420,
    words_per_line: 3,
    sub_box_style: "pill",
    sub_box_color: "#000000",
    sub_box_alpha: 0.85,
  },
  backgroundMode: "green_screen",
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Captions"
        component={Captions}
        durationInFrames={210} // 7 seconds @ 30fps
        fps={30}
        width={1080}
        height={1920}
        defaultProps={defaultSampleProps}
      />
    </>
  );
};
