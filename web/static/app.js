// DZ Subtitles AI - Multilingual & Interactive Comic Studio Controller
document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const fileInfo = document.getElementById("fileInfo");
  const fileName = document.getElementById("fileName");
  const fileSize = document.getElementById("fileSize");
  const fileIconSymbol = document.getElementById("fileIconSymbol");
  const removeFileBtn = document.getElementById("removeFileBtn");

  const startBtn = document.getElementById("startBtn");
  const reRenderBtn = document.getElementById("reRenderBtn");
  const progressContainer = document.getElementById("progressContainer");
  const progressBar = document.getElementById("progressBar");
  const progressPercentage = document.getElementById("progressPercentage");
  const progressStatus = document.getElementById("progressStatus");
  const progressStepBadge = document.getElementById("progressStepBadge");
  const emptyState = document.getElementById("emptyState");
  const videoContainer = document.getElementById("videoContainer");
  const resultVideo = document.getElementById("resultVideo");
  const editorContainer = document.getElementById("editorContainer");
  const segmentsList = document.getElementById("segmentsList");

  // Downloads
  const downloadVideoBtn = document.getElementById("downloadVideoBtn");
  const downloadAssBtn = document.getElementById("downloadAssBtn");
  const downloadSrtBtn = document.getElementById("downloadSrtBtn");
  const downloadJsonBtn = document.getElementById("downloadJsonBtn");

  // Customization Form Controls
  const dialectHint = document.getElementById("dialectHint");
  const alignment = document.getElementById("alignment");
  const marginV = document.getElementById("marginV");
  const marginVVal = document.getElementById("marginVVal");
  const fontName = document.getElementById("fontName");
  const fontSize = document.getElementById("fontSize");
  const fontSizeVal = document.getElementById("fontSizeVal");
  const wordsPerLine = document.getElementById("wordsPerLine");
  const animationStyle = document.getElementById("animationStyle");
  const primaryColor = document.getElementById("primaryColor");
  const primaryColorText = document.getElementById("primaryColorText");
  const highlightColor = document.getElementById("highlightColor");
  const highlightColorText = document.getElementById("highlightColorText");
  const backgroundMode = document.getElementById("backgroundMode");
  const customColorGroup = document.getElementById("customColorGroup");
  const customColorHex = document.getElementById("customColorHex");
  const customColorText = document.getElementById("customColorText");
  const aspectRatio = document.getElementById("aspectRatio");
  const apiKey = document.getElementById("apiKey");
  const presetButtons = document.querySelectorAll(".comic-preset-btn");

  // Theme & Language
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const themeLabel = document.getElementById("themeLabel");
  const langButtons = document.querySelectorAll(".lang-btn");

  // Phone Simulation Elements
  const platformTabs = document.querySelectorAll(".platform-tab");
  const platformTopBar = document.getElementById("platformTopBar");
  const liveSubtitleContainer = document.getElementById("liveSubtitleContainer");
  const liveSubtitleBox = document.getElementById("liveSubtitleBox");
  const subWord1 = document.getElementById("subWord1");
  const subWord2 = document.getElementById("subWord2");
  const subWord3 = document.getElementById("subWord3");
  const posSnapButtons = document.querySelectorAll(".pos-snap-btn");

  // Guide Modal
  const guideBtn = document.getElementById("guideBtn");
  const guideModal = document.getElementById("guideModal");
  const closeGuideBtn = document.getElementById("closeGuideBtn");

  // State
  let currentFile = null;
  let currentTaskId = null;
  let currentTranscription = null;
  let currentLang = localStorage.getItem("dz_subtitles_lang") || "en";
  let currentTheme = localStorage.getItem("dz_subtitles_theme") || "dark";
  let currentPlatform = "tiktok";

  // MULTILINGUAL TRANSLATION DICTIONARY
  const TRANSLATIONS = {
    en: {
      header_badge: "STUDIO",
      brand_tagline: "Auto Animated Subtitles & Safe-Zone Phone Simulation",
      btn_guide: "Guide",
      studio_title: "Studio & Output Preview",
      studio_subtitle: "GENERATOR",
      dropzone_title: "Drag & drop Audio or Video here",
      dropzone_formats: "Supports MP3, WAV, AAC, MP4, MOV, MKV, WebM",
      btn_browse: "Browse Media",
      progress_idle: "Ready for processing...",
      dl_video: "Video (MP4)",
      dl_ass: "ASS Animated",
      dl_srt: "SRT File",
      dl_json: "JSON Timings",
      empty_title: "Ready to Generate Viral Captions",
      empty_desc: "Upload an audio or video file. AI transcribes speech with exact millisecond word timestamps and burns viral animated subtitles in your chosen style.",
      editor_title: "Word & Timing Editor",
      btn_rerender: "Re-render Edits",
      customization_title: "Subtitle & Video Customization",
      customization_badge: "CONTROLS",
      sim_heading: "Phone Simulation (Safe-Zone Preview)",
      sim_subscribe: "Follow",
      sim_caption: "Keep captions safely above this section so UI never covers them! 🚀",
      sim_safe_zone: "SAFE SUBTITLE ZONE",
      pos_quick: "Position Snap:",
      pos_top: "Top",
      pos_middle: "Middle",
      pos_safe_bottom: "Safe Bottom",
      presets_title: "Viral Style Presets",
      ctrl_lang: "Speech Language",
      ctrl_pos: "Subtitle Position",
      ctrl_margin: "Vertical Margin",
      ctrl_font: "Font Family",
      ctrl_fontsize: "Font Size",
      ctrl_anim: "Animation Style",
      ctrl_textcolor: "Main Text Color",
      ctrl_highlight: "Active Word Highlight",
      ctrl_words: "Words Per Line",
      ctrl_aspect: "Aspect Ratio",
      ctrl_bg: "Background Canvas",
      ctrl_customcolor: "Custom Color",
      ctrl_apikey: "Gemini API Key (Optional Override)",
      tag_optional: "Preconfigured on server",
      btn_generate: "GENERATE ANIMATED SUBTITLES",
      modal_guide_title: "Video Editing & Safe-Zone Guide",
      guide_capcut: "Add the generated subtitle video as an <strong>Overlay</strong> above your main video. Select <strong>Remove BG</strong> > <strong>Chroma Key</strong>, click the green background with the color picker, and set Intensity to 15-20%.",
      guide_premiere: "Place the green-screen video on a track above your media. Search for the <strong>Ultra Key</strong> effect in Effects, apply it to the subtitle clip, and pick the green color using the Eyedropper tool.",
      guide_davinci: "In the Edit or Color page, use the <strong>3D Keyer</strong> or in Fusion use the <strong>Delta Keyer</strong> node to key out the green screen background instantly.",
      guide_black: "If you select Black Screen, no chroma keying is needed! Simply change the video layer's <strong>Blending Mode</strong> to <strong>Screen</strong> in CapCut, Premiere, or Final Cut.",
      guide_safezone: "Always ensure subtitles are positioned at least 260px-320px from the bottom to prevent creator profile handles, follow buttons, captions, and the audio title from obscuring your text.",
      step_1: "1/4: Uploading & AI speech analysis in progress...",
      step_2: "2/4: Word timestamps extracted! Building animations...",
      step_3: "3/4: Rendering animated video with FFmpeg...",
      step_4: "✅ Complete! Preview and download your video below.",
      alert_no_file: "Please upload an audio or video file first!"
    },
    fr: {
      header_badge: "STUDIO",
      brand_tagline: "Générateur de sous-titres animés avec simulation smartphone et zones sécurisées",
      btn_guide: "Guide",
      studio_title: "Studio & Aperçu du Résultat",
      studio_subtitle: "GÉNÉRATEUR",
      dropzone_title: "Glissez votre fichier Audio ou Vidéo ici",
      dropzone_formats: "Prend en charge MP3, WAV, AAC, MP4, MOV, MKV, WebM",
      btn_browse: "Parcourir",
      progress_idle: "Prêt pour le traitement...",
      dl_video: "Vidéo (MP4)",
      dl_ass: "ASS Animé",
      dl_srt: "Fichier SRT",
      dl_json: "Horodatage JSON",
      empty_title: "Prêt à créer des sous-titres viraux",
      empty_desc: "Importez un fichier audio ou vidéo. L'IA transcrit la parole avec horodatage mot par mot et applique des sous-titres animés selon votre style.",
      editor_title: "Éditeur de mots & minutage",
      btn_rerender: "Re-rendre les modifs",
      customization_title: "Personnalisation des Sous-titres & Vidéo",
      customization_badge: "RÉGLAGES",
      sim_heading: "Simulation Smartphone (Aperçu des zones)",
      sim_subscribe: "Suivre",
      sim_caption: "Gardez les sous-titres au-dessus de cette zone pour éviter tout masquage ! 🚀",
      sim_safe_zone: "ZONE SÛRE POUR SOUS-TITRES",
      pos_quick: "Alignement rapide :",
      pos_top: "Haut",
      pos_middle: "Milieu",
      pos_safe_bottom: "Bas sécurisé",
      presets_title: "Préréglages de Style Viraux",
      ctrl_lang: "Langue du contenu",
      ctrl_pos: "Position des sous-titres",
      ctrl_margin: "Marge verticale",
      ctrl_font: "Police d'écriture",
      ctrl_fontsize: "Taille de police",
      ctrl_anim: "Style d'animation",
      ctrl_textcolor: "Couleur du texte",
      ctrl_highlight: "Couleur du mot actif",
      ctrl_words: "Mots par ligne",
      ctrl_aspect: "Format d'image",
      ctrl_bg: "Arrière-plan vidéo",
      ctrl_customcolor: "Couleur personnalisée",
      ctrl_apikey: "Clé API Gemini (Optionnel)",
      tag_optional: "Préconfiguré sur serveur",
      btn_generate: "GÉNÉRER LES SOUS-TITRES ANIMÉS",
      modal_guide_title: "Guide de montage & Zones sécurisées",
      guide_capcut: "Ajoutez la vidéo générée en tant que <strong>Superposition (Overlay)</strong>. Allez dans <strong>Supprimer l'arrière-plan</strong> > <strong>Chroma Key</strong>, sélectionnez le vert avec la pipette et réglez l'intensité à 15-20%.",
      guide_premiere: "Placez la vidéo sur une piste au-dessus de votre média. Cherchez l'effet <strong>Ultra Key</strong>, appliquez-le au clip de sous-titres et sélectionnez le fond vert avec la pipette.",
      guide_davinci: "Dans la page Montage ou Couleur, utilisez <strong>3D Keyer</strong> ou dans Fusion le nœud <strong>Delta Keyer</strong> pour supprimer le fond vert instantanément.",
      guide_black: "Si vous choisissez le Fond Noir, aucun chroma key n'est nécessaire ! Changez simplement le <strong>Mode de fusion</strong> de la piste sur <strong>Superposition / Screen</strong>.",
      guide_safezone: "Assurez-vous toujours que les sous-titres sont placés à au moins 260px-320px du bas pour éviter que le profil, le bouton suivre et la description ne les recouvrent.",
      step_1: "1/4: Téléversement et analyse audio par l'IA en cours...",
      step_2: "2/4: Mots et horodatages extraits ! Création des animations...",
      step_3: "3/4: Rendu de la vidéo animée avec FFmpeg...",
      step_4: "✅ Terminé avec succès ! Visionnez et téléchargez ci-dessous.",
      alert_no_file: "Veuillez d'abord téléverser un fichier audio ou vidéo !"
    },
    ar: {
      header_badge: "استوديو",
      brand_tagline: "مولّد الترجمة المتحركة التلقائية مع محاكاة شاشة الهاتف ومناطق الأمان",
      btn_guide: "دليل الاستخدام",
      studio_title: "معاينة الاستوديو والنتيجة",
      studio_subtitle: "المولّد",
      dropzone_title: "اسحب ملف الصوت أو الفيديو هنا",
      dropzone_formats: "يدعم MP3، WAV، AAC، MP4، MOV، MKV، WebM",
      btn_browse: "استعراض الملفات",
      progress_idle: "جاهز لبدء المعالجة...",
      dl_video: "تحميل الفيديو (MP4)",
      dl_ass: "ملف ASS المتحرك",
      dl_srt: "ملف SRT",
      dl_json: "توقيتات JSON",
      empty_title: "جاهز لتوليد ترجمات متحركة احترافية",
      empty_desc: "قم برفع ملف صوتي أو فيديو. سيقوم الذكاء الاصطناعي بتوليد الترجمة المتزامنة مع كل كلمة وتطبيق الأنيميشن مع كروما خضراء أو دمج مباشر.",
      editor_title: "محرر ومراجعة الكلمات والتوقيت",
      btn_rerender: "إعادة الرندر بالتعديلات",
      customization_title: "تخصيص وإعدادات الترجمة والفيديو",
      customization_badge: "التحكم",
      sim_heading: "محاكاة الهاتف (مناطق الأمان للريلز والتيك توك)",
      sim_subscribe: "متابعة",
      sim_caption: "احرص على أن تكون الترجمة فوق هذه المنطقة حتى لا تحجبها واجهة التطبيق! 🚀",
      sim_safe_zone: "منطقة الأمان للترجمة",
      pos_quick: "محاذاة سريعة:",
      pos_top: "أعلى",
      pos_middle: "المنتصف",
      pos_safe_bottom: "أسفل آمن",
      presets_title: "أنماط جاهزة سريعة",
      ctrl_lang: "لغة المحتوى الصوتي",
      ctrl_pos: "موضع الترجمة",
      ctrl_margin: "الهامش العمودي",
      ctrl_font: "نوع الخط",
      ctrl_fontsize: "حجم الخط",
      ctrl_anim: "نمط الأنيميشن (الحركة)",
      ctrl_textcolor: "لون النص الرئيسي",
      ctrl_highlight: "لون الكلمة النشطة",
      ctrl_words: "عدد الكلمات في السطر",
      ctrl_aspect: "أبعاد الفيديو",
      ctrl_bg: "خلفية الفيديو",
      ctrl_customcolor: "لون مخصص",
      ctrl_apikey: "مفتاح Gemini API (اختياري)",
      tag_optional: "مضبوط مسبقاً على السيرفر",
      btn_generate: "توليد الترجمة المتحركة الآن",
      modal_guide_title: "دليل المونتاج ومناطق الأمان للهواتف",
      guide_capcut: "أضف فيديو الترجمة كطبقة علوية (Overlay) فوق الفيديو الخاص بك. اذهب إلى <strong>Remove BG</strong> واختر <strong>Chroma Key</strong>، وحدد اللون الأخضر بالقطارة وضع الشدة على 15-20%.",
      guide_premiere: "ضع فيديو الكروما الخضراء فوق الفيديو في الـ Timeline. في قائمة Effects ابحث عن تأثير <strong>Ultra Key</strong> وقم بتطبيقه على طبقة الترجمة ثم حدد اللون الأخضر.",
      guide_davinci: "في صفحة Edit أو Color، استخدم أداة <strong>3D Keyer</strong> أو في Fusion استخدم عقدة <strong>Delta Keyer</strong> لإزالة اللون الأخضر بنقرة واحدة.",
      guide_black: "إذا اخترت وضع الشاشة السوداء، لا حاجة للكروما! ما عليك سوى تغيير الـ <strong>Blending Mode</strong> للطبقة إلى <strong>Screen</strong> في أي برنامج مونتاج.",
      guide_safezone: "احرص دائماً على وضع الترجمة على مسافة لا تقل عن 260px-320px من أسفل الشاشة حتى لا تغطيها بيانات صاحب الحساب، زر المتابعة، والوصف الموسيقي.",
      step_1: "1/4: جاري رفع الملف وتحليله بالذكاء الاصطناعي...",
      step_2: "2/4: تم استخراج الكلمات والتوقيتات! جاري بناء الأنيميشن...",
      step_3: "3/4: جاري رندر الفيديو بواسطة FFmpeg مع الخطوط المحددة...",
      step_4: "✅ اكتمل التوليد بنجاح! يمكنك الآن مشاهدة وتحميل النتيجة.",
      alert_no_file: "الرجاء رفع ملف صوتي أو فيديو أولاً!"
    }
  };

  // APPLY LANGUAGE FUNCTION
  function applyLanguage(lang) {
    if (!TRANSLATIONS[lang]) lang = "en";
    currentLang = lang;
    localStorage.setItem("dz_subtitles_lang", lang);

    document.documentElement.lang = lang;
    document.documentElement.dir = (lang === "ar") ? "rtl" : "ltr";

    langButtons.forEach(btn => {
      btn.classList.toggle("active", btn.dataset.lang === lang);
    });

    // Translate all elements with data-i18n
    const dict = TRANSLATIONS[lang];
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      if (dict[key]) {
        el.innerHTML = dict[key];
      }
    });
  }

  // Language buttons click listener
  langButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      applyLanguage(btn.dataset.lang);
    });
  });

  // THEME MANAGEMENT (Default to Dark Mode!)
  function applyTheme(theme) {
    currentTheme = theme;
    localStorage.setItem("dz_subtitles_theme", theme);
    document.documentElement.className = (theme === "light") ? "theme-light" : "theme-dark";
    if (themeLabel) {
      themeLabel.innerText = (theme === "light") ? "Light" : "Dark";
    }
  }

  themeToggleBtn.addEventListener("click", () => {
    const nextTheme = (currentTheme === "dark") ? "light" : "dark";
    applyTheme(nextTheme);
  });

  // RESTORE SAVED GEMINI API KEY
  const savedApiKey = localStorage.getItem("dz_gemini_api_key");
  if (savedApiKey) {
    apiKey.value = savedApiKey;
  }
  apiKey.addEventListener("input", () => {
    localStorage.setItem("dz_gemini_api_key", apiKey.value.trim());
  });

  // STYLE PRESETS
  const PRESETS = {
    gold: { primary: "#FFFFFF", highlight: "#FFE600", font: "Cairo", anim: "karaoke_pop", align: "2", margin: 280 },
    cyan: { primary: "#FFFFFF", highlight: "#00F0FF", font: "Tajawal", anim: "karaoke_pop", align: "2", margin: 280 },
    coral: { primary: "#FFFFFF", highlight: "#FF3366", font: "Cairo", anim: "karaoke_pop", align: "2", margin: 280 },
    lime: { primary: "#FFFFFF", highlight: "#00FF66", font: "Almarai", anim: "word_reveal", align: "2", margin: 280 },
    comic: { primary: "#F5EEDB", highlight: "#EAA838", font: "Plus Jakarta Sans", anim: "box_highlight", align: "2", margin: 280 },
    white: { primary: "#F0F0F0", highlight: "#FACC15", font: "Cairo", anim: "classic_line", align: "2", margin: 280 }
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
        alignment.value = p.align;
        marginV.value = p.margin;
        marginVVal.innerText = p.margin + "px";
        updateLiveSubtitlePreview();
      }
    });
  });

  // PHONE PLATFORM TABS
  platformTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      platformTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      currentPlatform = tab.dataset.platform;
      updatePlatformTopNav();
    });
  });

  function updatePlatformTopNav() {
    if (!platformTopBar) return;
    if (currentPlatform === "tiktok") {
      platformTopBar.innerHTML = `
        <div class="nav-content tiktok-top-nav">
          <span class="top-nav-link">Live</span>
          <span class="top-nav-link">Following</span>
          <span class="top-nav-link active">For You</span>
          <svg class="top-nav-search" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        </div>`;
    } else if (currentPlatform === "reels") {
      platformTopBar.innerHTML = `
        <div class="nav-content tiktok-top-nav" style="justify-content: space-between;">
          <span style="font-weight: 900; font-size: 11px; color: #fff;">Reels</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
        </div>`;
    } else if (currentPlatform === "shorts") {
      platformTopBar.innerHTML = `
        <div class="nav-content tiktok-top-nav" style="justify-content: space-between;">
          <span style="font-weight: 900; font-size: 11px; color: #fff; display: flex; align-items: center; gap: 4px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="#ff0000"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
            Shorts
          </span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        </div>`;
    }
  }

  // LIVE SUBTITLE PREVIEW IN PHONE SIMULATOR
  function updateLiveSubtitlePreview() {
    if (!liveSubtitleContainer || !liveSubtitleBox) return;

    // Font and styling
    liveSubtitleBox.style.fontFamily = fontName.value;
    const scaledSize = Math.max(9, Math.round(parseInt(fontSize.value) * 0.19));
    liveSubtitleBox.style.fontSize = scaledSize + "px";

    subWord1.style.color = primaryColor.value;
    subWord2.style.color = highlightColor.value;
    subWord3.style.color = primaryColor.value;

    // Animation visual distinction
    if (animationStyle.value === "box_highlight") {
      subWord2.style.background = highlightColor.value;
      subWord2.style.color = "#000000";
      subWord2.style.padding = "0 3px";
      subWord2.style.borderRadius = "3px";
    } else {
      subWord2.style.background = "none";
      subWord2.style.color = highlightColor.value;
      subWord2.style.padding = "0";
    }

    // Position in Phone
    const alignVal = alignment.value;
    const marginPixels = parseInt(marginV.value);

    if (alignVal === "8") {
      // Top
      liveSubtitleContainer.style.top = "38px";
      liveSubtitleContainer.style.bottom = "auto";
      liveSubtitleContainer.style.transform = "none";
    } else if (alignVal === "5") {
      // Center
      liveSubtitleContainer.style.top = "48%";
      liveSubtitleContainer.style.bottom = "auto";
      liveSubtitleContainer.style.transform = "translateY(-50%)";
    } else {
      // Bottom (Safe Zone)
      // Map 40-500px Ass margin to 45px - 145px inside 290px phone
      const phoneBottomPx = Math.round(55 + (marginPixels / 500) * 80);
      liveSubtitleContainer.style.top = "auto";
      liveSubtitleContainer.style.bottom = phoneBottomPx + "px";
      liveSubtitleContainer.style.transform = "none";
    }

    // Update Quick Position Snap Button Highlight
    posSnapButtons.forEach(btn => {
      btn.classList.toggle("active", btn.dataset.pos === alignVal);
    });
  }

  // QUICK POSITION SNAP BUTTONS
  posSnapButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const pos = btn.dataset.pos;
      alignment.value = pos;
      if (pos === "2") {
        marginV.value = 280;
        marginVVal.innerText = "280px";
      } else if (pos === "8") {
        marginV.value = 90;
        marginVVal.innerText = "90px";
      }
      updateLiveSubtitlePreview();
    });
  });

  // FORM INPUT LISTENERS FOR INSTANT PREVIEW
  alignment.addEventListener("change", () => {
    if (alignment.value === "2" && parseInt(marginV.value) < 150) {
      marginV.value = 280;
      marginVVal.innerText = "280px";
    }
    updateLiveSubtitlePreview();
  });

  marginV.addEventListener("input", (e) => {
    marginVVal.innerText = e.target.value + "px";
    requestAnimationFrame(updateLiveSubtitlePreview);
  });

  fontSize.addEventListener("input", (e) => {
    fontSizeVal.innerText = e.target.value + "px";
    requestAnimationFrame(updateLiveSubtitlePreview);
  });

  fontName.addEventListener("change", updateLiveSubtitlePreview);
  animationStyle.addEventListener("change", updateLiveSubtitlePreview);

  primaryColor.addEventListener("input", (e) => {
    primaryColorText.innerText = e.target.value.toUpperCase();
    updateLiveSubtitlePreview();
  });

  highlightColor.addEventListener("input", (e) => {
    highlightColorText.innerText = e.target.value.toUpperCase();
    updateLiveSubtitlePreview();
  });

  // QUICK SWATCH CLICKS
  document.querySelectorAll(".swatch-dot").forEach(dot => {
    dot.addEventListener("click", () => {
      const target = dot.dataset.target;
      const color = dot.dataset.color;
      if (target === "primary") {
        primaryColor.value = color;
        primaryColorText.innerText = color;
      } else if (target === "highlight") {
        highlightColor.value = color;
        highlightColorText.innerText = color;
      }
      updateLiveSubtitlePreview();
    });
  });

  // BACKGROUND MODE TOGGLE
  backgroundMode.addEventListener("change", () => {
    if (backgroundMode.value === "custom") {
      customColorGroup.style.display = "flex";
    } else {
      customColorGroup.style.display = "none";
    }
  });

  customColorHex.addEventListener("input", (e) => {
    customColorText.innerText = e.target.value.toUpperCase();
  });

  // GUIDE MODAL TOGGLES
  guideBtn.addEventListener("click", () => guideModal.classList.remove("hidden"));
  closeGuideBtn.addEventListener("click", () => guideModal.classList.add("hidden"));
  guideModal.addEventListener("click", (e) => {
    if (e.target === guideModal) guideModal.classList.add("hidden");
  });

  // FILE UPLOAD AND DRAG-AND-DROP HANDLERS
  function setFile(file) {
    if (!file) return;
    currentFile = file;
    fileName.innerText = file.name;
    fileSize.innerText = (file.size / (1024 * 1024)).toFixed(2) + " MB";

    const isVideo = file.type.startsWith("video/") || /\.(mp4|mov|mkv|webm)$/i.test(file.name);
    fileIconSymbol.innerHTML = isVideo ? `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect>
        <line x1="7" y1="2" x2="7" y2="22"></line>
        <line x1="17" y1="2" x2="17" y2="22"></line>
        <line x1="2" y1="12" x2="22" y2="12"></line>
      </svg>` : `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <path d="M9 18V5l12-2v13"></path>
        <circle cx="6" cy="18" r="3"></circle>
        <circle cx="18" cy="16" r="3"></circle>
      </svg>`;

    if (isVideo) {
      backgroundMode.value = "original_video";
    } else {
      backgroundMode.value = "green_screen";
    }
    backgroundMode.dispatchEvent(new Event("change"));

    fileInfo.classList.remove("hidden");
    document.querySelector(".dropzone-body").classList.add("hidden");
  }

  function clearFile() {
    currentFile = null;
    fileInput.value = "";
    fileInfo.classList.add("hidden");
    document.querySelector(".dropzone-body").classList.remove("hidden");
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

  // PROGRESS TRACKER HELPER
  function updateProgress(percent, stepText, message) {
    progressContainer.classList.remove("hidden");
    progressBar.style.width = percent + "%";
    progressPercentage.innerText = percent + "%";
    progressStepBadge.innerText = stepText;
    progressStatus.innerText = message;
  }

  // SUBTITLE EDITOR POPULATION
  function renderEditor(transcription) {
    segmentsList.innerHTML = "";
    if (!transcription || !transcription.segments || transcription.segments.length === 0) {
      editorContainer.classList.add("hidden");
      return;
    }

    // Also update phone simulation text with actual first segment words!
    const firstWords = transcription.segments[0].words;
    if (firstWords && firstWords.length >= 3) {
      subWord1.innerText = firstWords[0].word;
      subWord2.innerText = firstWords[1].word;
      subWord3.innerText = firstWords[2].word;
    }

    transcription.segments.forEach((seg, idx) => {
      const item = document.createElement("div");
      item.className = "comic-seg-item";

      const timeSpan = document.createElement("span");
      timeSpan.className = "comic-seg-time";
      timeSpan.innerText = `${seg.start.toFixed(2)}s - ${seg.end.toFixed(2)}s`;

      const input = document.createElement("input");
      input.className = "comic-seg-input";
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

  // GENERATE SUBTITLES FLOW
  startBtn.addEventListener("click", async () => {
    const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
    if (!currentFile) {
      alert(dict.alert_no_file);
      return;
    }

    startBtn.disabled = true;
    emptyState.classList.add("hidden");
    videoContainer.classList.add("hidden");

    try {
      // Step 1: Upload & Transcribe
      updateProgress(25, "Step 1/4", dict.step_1);

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
        throw new Error(err.detail || "Transcription failed");
      }

      const transcribeData = await transcribeRes.json();
      currentTaskId = transcribeData.task_id;
      currentTranscription = transcribeData.transcription;

      updateProgress(65, "Step 2/4", dict.step_2);
      renderEditor(currentTranscription);

      // Step 2: Render Subtitles and Video
      await triggerRender();

    } catch (err) {
      console.error(err);
      alert("Error: " + err.message);
      progressContainer.classList.add("hidden");
      emptyState.classList.remove("hidden");
    } finally {
      startBtn.disabled = false;
    }
  });

  // RE-RENDER WITH EDITED SUBTITLES
  reRenderBtn.addEventListener("click", async () => {
    if (!currentTaskId || !currentTranscription) return;
    reRenderBtn.disabled = true;
    const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
    updateProgress(50, "Re-rendering", dict.step_3);
    try {
      await triggerRender();
    } catch (err) {
      alert("Render failed: " + err.message);
    } finally {
      reRenderBtn.disabled = false;
    }
  });

  async function triggerRender() {
    const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
    updateProgress(80, "Step 3/4", dict.step_3);

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
      margin_v: parseInt(marginV.value),
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
      throw new Error(err.detail || "Rendering failed");
    }

    const data = await renderRes.json();
    updateProgress(100, "Step 4/4", dict.step_4);

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

  // INITIAL SETUP CALLS
  applyLanguage(currentLang);
  applyTheme(currentTheme);
  updatePlatformTopNav();
  updateLiveSubtitlePreview();
});
