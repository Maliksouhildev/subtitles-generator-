// DZ Subtitles AI - Client Controller
document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const fileInfo = document.getElementById("fileInfo");
  const fileName = document.getElementById("fileName");
  const fileSize = document.getElementById("fileSize");
  const fileIcon = document.getElementById("fileIcon");
  const removeFileBtn = document.getElementById("removeFileBtn");

  const startBtn = document.getElementById("startBtn");
  const reRenderBtn = document.getElementById("reRenderBtn");
  const progressContainer = document.getElementById("progressContainer");
  const progressBar = document.getElementById("progressBar");
  const progressStatus = document.getElementById("progressStatus");
  const emptyState = document.getElementById("emptyState");
  const videoContainer = document.getElementById("videoContainer");
  const resultVideo = document.getElementById("resultVideo");
  const editorContainer = document.getElementById("editorContainer");
  const segmentsList = document.getElementById("segmentsList");

  // Download links
  const downloadVideoBtn = document.getElementById("downloadVideoBtn");
  const downloadAssBtn = document.getElementById("downloadAssBtn");
  const downloadSrtBtn = document.getElementById("downloadSrtBtn");
  const downloadJsonBtn = document.getElementById("downloadJsonBtn");

  // Form Controls
  const backgroundMode = document.getElementById("backgroundMode");
  const customColorGroup = document.getElementById("customColorGroup");
  const customColorHex = document.getElementById("customColorHex");
  const aspectRatio = document.getElementById("aspectRatio");
  const fontName = document.getElementById("fontName");
  const fontSize = document.getElementById("fontSize");
  const fontSizeVal = document.getElementById("fontSizeVal");
  const primaryColor = document.getElementById("primaryColor");
  const primaryColorText = document.getElementById("primaryColorText");
  const highlightColor = document.getElementById("highlightColor");
  const highlightColorText = document.getElementById("highlightColorText");
  const animationStyle = document.getElementById("animationStyle");
  const wordsPerLine = document.getElementById("wordsPerLine");
  const alignment = document.getElementById("alignment");
  const dialectHint = document.getElementById("dialectHint");
  const apiKey = document.getElementById("apiKey");
  const presetButtons = document.querySelectorAll(".btn-preset");

  // Guide Modal
  const guideBtn = document.getElementById("guideBtn");
  const guideModal = document.getElementById("guideModal");
  const closeGuideBtn = document.getElementById("closeGuideBtn");

  let currentFile = null;
  let currentTaskId = null;
  let currentTranscription = null;

  // Restore saved API Key
  const savedApiKey = localStorage.getItem("dz_gemini_api_key");
  if (savedApiKey) {
    apiKey.value = savedApiKey;
  }
  apiKey.addEventListener("input", () => {
    localStorage.setItem("dz_gemini_api_key", apiKey.value.trim());
  });

  // Style Presets
  const PRESETS = {
    gold: { primary: "#FFFFFF", highlight: "#FFE600", font: "Cairo", anim: "karaoke_pop" },
    cyan: { primary: "#FFFFFF", highlight: "#00F0FF", font: "Tajawal", anim: "karaoke_pop" },
    coral: { primary: "#FFFFFF", highlight: "#FF3366", font: "Cairo", anim: "karaoke_pop" },
    lime: { primary: "#FFFFFF", highlight: "#00FF66", font: "Almarai", anim: "word_reveal" },
    white: { primary: "#F0F0F0", highlight: "#FACC15", font: "Cairo", anim: "classic_line" }
  };

  presetButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      presetButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const p = PRESETS[btn.dataset.preset];
      if (p) {
        primaryColor.value = p.primary;
        primaryColorText.innerText = p.primary;
        highlightColor.value = p.highlight;
        highlightColorText.innerText = p.highlight;
        fontName.value = p.font;
        animationStyle.value = p.anim;
      }
    });
  });

  // Slider change
  fontSize.addEventListener("input", (e) => {
    fontSizeVal.innerText = e.target.value;
  });

  // Color Pickers
  primaryColor.addEventListener("input", (e) => {
    primaryColorText.innerText = e.target.value.toUpperCase();
  });
  highlightColor.addEventListener("input", (e) => {
    highlightColorText.innerText = e.target.value.toUpperCase();
  });

  // Background mode toggle
  backgroundMode.addEventListener("change", () => {
    if (backgroundMode.value === "custom") {
      customColorGroup.style.display = "flex";
    } else {
      customColorGroup.style.display = "none";
    }
  });

  // Modal events
  guideBtn.addEventListener("click", () => guideModal.classList.remove("hidden"));
  closeGuideBtn.addEventListener("click", () => guideModal.classList.add("hidden"));
  guideModal.addEventListener("click", (e) => {
    if (e.target === guideModal) guideModal.classList.add("hidden");
  });

  // File Upload Handlers
  function setFile(file) {
    if (!file) return;
    currentFile = file;
    fileName.innerText = file.name;
    fileSize.innerText = (file.size / (1024 * 1024)).toFixed(2) + " MB";
    const isVideo = file.type.startsWith("video/") || /\.(mp4|mov|mkv|webm)$/i.test(file.name);
    fileIcon.innerText = isVideo ? "🎬" : "🎵";

    if (isVideo) {
      backgroundMode.value = "original_video";
    } else {
      backgroundMode.value = "green_screen";
    }
    backgroundMode.dispatchEvent(new Event("change"));

    fileInfo.classList.remove("hidden");
    document.querySelector(".upload-content").classList.add("hidden");
  }

  function clearFile() {
    currentFile = null;
    fileInput.value = "";
    fileInfo.classList.add("hidden");
    document.querySelector(".upload-content").classList.remove("hidden");
  }

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) setFile(e.target.files[0]);
  });

  removeFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    clearFile();
  });

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) setFile(e.dataTransfer.files[0]);
  });

  // Progress Update Helper
  function updateProgress(percent, message) {
    progressContainer.classList.remove("hidden");
    progressBar.style.width = percent + "%";
    progressStatus.innerText = message;
  }

  // Populate Subtitle Editor
  function renderEditor(transcription) {
    segmentsList.innerHTML = "";
    if (!transcription || !transcription.segments) return;

    transcription.segments.forEach((seg, idx) => {
      const item = document.createElement("div");
      item.className = "segment-item";

      const timeSpan = document.createElement("span");
      timeSpan.className = "segment-time";
      timeSpan.innerText = `[${seg.start.toFixed(2)}s - ${seg.end.toFixed(2)}s]`;

      const input = document.createElement("input");
      input.className = "segment-input";
      input.type = "text";
      input.value = seg.text;
      input.dataset.index = idx;

      input.addEventListener("input", (e) => {
        const segIdx = parseInt(e.target.dataset.index);
        transcription.segments[segIdx].text = e.target.value;
      });

      item.appendChild(timeSpan);
      item.appendChild(input);
      segmentsList.appendChild(item);
    });

    editorContainer.classList.remove("hidden");
  }

  // Start Generation Action
  startBtn.addEventListener("click", async () => {
    if (!currentFile) {
      alert("الرجاء رفع ملف صوتي أو فيديو أولاً!");
      return;
    }

    startBtn.disabled = true;
    emptyState.classList.add("hidden");
    videoContainer.classList.add("hidden");

    try {
      // Step 1: Upload & Transcribe
      updateProgress(25, "1/4: جاري رفع الملف وتحليله بالذكاء الاصطناعي (Gemini Darija)...");

      const formData = new FormData();
      formData.append("file", currentFile);
      if (apiKey.value.trim()) {
        formData.append("api_key", apiKey.value.trim());
      }
      formData.append("dialect_hint", dialectHint.value);

      const transcribeRes = await fetch("/api/transcribe", {
        method: "POST",
        body: formData
      });

      if (!transcribeRes.ok) {
        const err = await transcribeRes.json();
        throw new Error(err.detail || "فشل التفريغ الصوتي بالذكاء الاصطناعي");
      }

      const transcribeData = await transcribeRes.json();
      currentTaskId = transcribeData.task_id;
      currentTranscription = transcribeData.transcription;

      updateProgress(65, "2/4: تم استخراج الكلمات والتوقيتات! جاري بناء الأنيميشن والرندر...");
      renderEditor(currentTranscription);

      // Step 2: Render Subtitles & Video
      await triggerRender();

    } catch (err) {
      console.error(err);
      alert("حدث خطأ أثناء المعالجة: " + err.message);
      progressContainer.classList.add("hidden");
      emptyState.classList.remove("hidden");
    } finally {
      startBtn.disabled = false;
    }
  });

  // Re-Render after editing subtitles or styles
  reRenderBtn.addEventListener("click", async () => {
    if (!currentTaskId || !currentTranscription) return;
    reRenderBtn.disabled = true;
    updateProgress(50, "جاري إعادة رندر الفيديو مع التعديلات الجديدة...");
    try {
      await triggerRender();
    } catch (err) {
      alert("فشل الرندر: " + err.message);
    } finally {
      reRenderBtn.disabled = false;
    }
  });

  async function triggerRender() {
    updateProgress(80, "3/4: جاري توليد الفيديو بواسطة FFmpeg مع الخطوط العربية...");

    const renderPayload = {
      task_id: currentTaskId,
      transcription_data: currentTranscription,
      font_name: fontName.value,
      font_size: parseInt(fontSize.value),
      primary_color: primaryColor.value,
      highlight_color: highlightColor.value,
      outline_color: "#000000",
      shadow_color: "#000000",
      outline_width: 3.5,
      shadow_depth: 2.0,
      alignment: parseInt(alignment.value),
      margin_v: alignment.value === "2" ? 90 : (alignment.value === "8" ? 90 : 0),
      words_per_line: parseInt(wordsPerLine.value),
      animation_style: animationStyle.value,
      background_mode: backgroundMode.value,
      custom_color_hex: customColorHex.value,
      aspect_ratio: aspectRatio.value
    };

    const renderRes = await fetch("/api/render", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(renderPayload)
    });

    if (!renderRes.ok) {
      const err = await renderRes.json();
      throw new Error(err.detail || "فشل رندر الفيديو");
    }

    const data = await renderRes.json();
    updateProgress(100, "✅ اكتمل التوليد بنجاح! يمكنك الآن مشاهدة وتحميل النتيجة.");

    // Update Player & Download buttons
    resultVideo.src = data.video_url;
    downloadVideoBtn.href = data.video_url;
    downloadAssBtn.href = data.ass_url;
    downloadSrtBtn.href = data.srt_url;
    downloadJsonBtn.href = data.json_url || `/api/download/${currentTaskId}/transcript.json`;

    videoContainer.classList.remove("hidden");
    resultVideo.load();
    resultVideo.play().catch(() => {});
  }
});
