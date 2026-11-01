// DZ Subtitles AI - Multilingual & Interactive Comic Studio Controller
document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements - Left Panel
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
  const downloadRemotionBtn = document.getElementById("downloadRemotionBtn");

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
  const animSpeed = document.getElementById("animSpeed");
  const animSpeedVal = document.getElementById("animSpeedVal");
  const speedChips = document.querySelectorAll(".speed-chip");
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

  // Header Controls: Theme & Language
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const themeLabel = document.getElementById("themeLabel");
  const langButtons = document.querySelectorAll(".lang-btn");

  // Phone Simulation Elements
  const phoneDevice = document.getElementById("phoneDevice");
  const phoneVideoBg = document.getElementById("phoneVideoBg");
  const dragTooltip = document.getElementById("dragTooltip");
  const platformTabs = document.querySelectorAll(".platform-tab");
  const platformTopBar = document.getElementById("platformTopBar");
  const phoneSidebar = document.getElementById("phoneSidebar");
  const phoneBottomOverlay = document.getElementById("phoneBottomOverlay");
  const liveSubtitleContainer = document.getElementById("liveSubtitleContainer");
  const liveSubtitleBox = document.getElementById("liveSubtitleBox");
  const subWord1 = document.getElementById("subWord1");
  const subWord2 = document.getElementById("subWord2");
  const subWord3 = document.getElementById("subWord3");

  // Custom Animation Select & Batch Queue Elements
  const animSelectWrap = document.getElementById("animSelectWrap");
  const animSelectTrigger = document.getElementById("animSelectTrigger");
  const animSelectLabel = document.getElementById("animSelectLabel");
  const animSelectLivePreview = document.getElementById("animSelectLivePreview");
  const animDropdownPanel = document.getElementById("animDropdownPanel");
  const animOptionRows = document.querySelectorAll(".anim-option-row");

  const progressEta = document.getElementById("progressEta");
  const queueSection = document.getElementById("queueSection");
  const queueItemsList = document.getElementById("queueItemsList");
  const queueCount = document.getElementById("queueCount");
  const clearQueueBtn = document.getElementById("clearQueueBtn");
  const queueAddBtn = document.getElementById("queueAddBtn");
  const addMoreFilesBtn = document.getElementById("addMoreFilesBtn");

  // Subtitle Background Box Controls
  const subBoxStyle = document.getElementById("subBoxStyle");
  const subBoxControls = document.getElementById("subBoxControls");
  const subBoxColor = document.getElementById("subBoxColor");
  const subBoxColorText = document.getElementById("subBoxColorText");
  const subBoxAlpha = document.getElementById("subBoxAlpha");
  const subBoxAlphaVal = document.getElementById("subBoxAlphaVal");

  // Guide Modal
  const guideBtn = document.getElementById("guideBtn");
  const guideModal = document.getElementById("guideModal");
  const closeGuideBtn = document.getElementById("closeGuideBtn");

  // Application State
  let currentFile = null;
  let currentTaskId = null;
  let currentTranscription = null;
  let currentLang = localStorage.getItem("dz_subtitles_lang") || "en";
  let currentTheme = localStorage.getItem("dz_subtitles_theme") || "dark";
  let currentPlatform = "tiktok";
  let batchQueue = [];
  let isProcessingBatch = false;

  // COMPLETE MULTILINGUAL TRANSLATION DICTIONARY (ZERO EMOJIS, CLEAN & PROFESSIONAL)
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
      badge_synced: "100% Synced",
      badge_shorts: "Shorts & Reels",
      badge_comic: "Neo-Comic Style",
      dl_video: "Video (MP4)",
      dl_ass: "ASS Animated",
      dl_srt: "SRT File",
      dl_json: "JSON Timings",
      dl_remotion: "Remotion (React)",
      empty_title: "Ready to Generate Viral Captions",
      empty_desc: "Upload an audio or video file. AI transcribes speech with exact millisecond word timestamps and burns viral animated subtitles in your chosen style.",
      editor_title: "Word & Timing Editor",
      btn_rerender: "Re-render Edits",
      customization_title: "Subtitle & Video Customization",
      customization_badge: "CONTROLS",
      sim_heading: "Phone Simulation",
      sim_safe_zone: "SAFE ZONE",
      pos_quick: "Position:",
      pos_top: "Top",
      pos_middle: "Middle",
      pos_safe_bottom: "Safe Bottom",
      presets_title: "Viral Style Presets",
      preset_gold: "TikTok Gold",
      preset_cyan: "Cyber Cyan",
      preset_coral: "Hot Coral",
      preset_lime: "Lime Punch",
      preset_comic: "Comic Pop",
      preset_white: "Classic White",
      ctrl_lang: "Speech Language",
      ctrl_pos: "Subtitle Position",
      ctrl_margin: "Vertical Margin",
      ctrl_font: "Font Family",
      ctrl_fontsize: "Font Size",
      ctrl_anim: "Animation Style",
      ctrl_animspeed: "Animation Speed",
      ctrl_textcolor: "Main Text Color",
      ctrl_highlight: "Active Word Highlight",
      ctrl_words: "Words Per Line",
      ctrl_aspect: "Aspect Ratio",
      ctrl_bg: "Background Canvas",
      ctrl_customcolor: "Custom Color",
      ctrl_apikey: "Gemini API Key (Optional)",
      tag_optional: "Preconfigured on server",
      btn_generate: "GENERATE ANIMATED SUBTITLES",
      modal_guide_title: "Video Editing & Safe-Zone Guide",
      guide_capcut: "Add the generated subtitle video as an <strong>Overlay</strong> above your main video. Select <strong>Remove BG</strong> > <strong>Chroma Key</strong>, click the green background with the color picker, and set Intensity to 15-20%.",
      guide_premiere: "Place the green-screen video on a track above your media. Search for the <strong>Ultra Key</strong> effect in Effects, apply it to the subtitle clip, and pick the green color using the Eyedropper tool.",
      guide_davinci: "In the Edit or Color page, use the <strong>3D Keyer</strong> or in Fusion use the <strong>Delta Keyer</strong> node to key out the green screen background instantly.",
      guide_black: "If you select Black Screen, no chroma keying is needed! Simply change the video layer's <strong>Blending Mode</strong> to <strong>Screen</strong> in CapCut, Premiere, or Final Cut.",
      guide_safezone: "Always ensure subtitles are positioned at least 260px-320px from the bottom to prevent creator profile handles, follow buttons, captions, and the audio title from obscuring your text.",
      step_1: "1/4: Uploading and analyzing speech audio...",
      step_2: "2/4: Word timestamps extracted! Generating animations...",
      step_3: "3/4: Rendering animated video with FFmpeg...",
      step_4: "Complete! Preview and download your video below.",
      alert_no_file: "Please upload an audio or video file first!",
      sim_tiktok_caption: "Keep captions safely above this section so UI never covers them!",
      sim_reels_caption: "Keep captions safely above this section so UI never covers them!",
      sim_shorts_caption: "Keep captions safely above this section so UI never covers them!",
      sim_follow: "Follow",
      sim_subscribe: "Subscribe",
      // Dropdown Options
      opt_lang_dz: "Algerian Darija (الدارجة الجزائرية - عربي)",
      opt_lang_latin: "Algerian Darija (Latin / Arabizi 3, 7, 9)",
      opt_lang_msa: "Modern Standard Arabic (العربية الفصحى)",
      opt_lang_fr: "French (Français)",
      opt_lang_en: "English",
      opt_pos_bottom: "Bottom (Safe Zone above UI)",
      opt_pos_center: "Center (Middle)",
      opt_pos_top: "Top (Header)",
      opt_anim_karaoke: "Hormozi Viral Pop",
      opt_anim_minimal: "Minimal Smooth Slide",
      opt_anim_cyber: "Cyberpunk Neon Jitter",
      opt_anim_comic: "Comic Bounce & Tilt",
      opt_anim_punch: "Viral Punch Snap",
      opt_anim_editorial: "Cinematic Smooth Fade",
      opt_anim_badge: "Badge Invert Pill",
      btn_save_preset: "+ Save Current",
      save_preset_title: "Save Custom Preset",
      save_preset_desc: "Save your current font, colors, animation, and position for future videos with zero login needed.",
      preset_name_label: "Preset Name",
      preset_name_placeholder: "e.g. My TikTok Viral, Gaming Shorts",
      btn_save: "Save Preset",
      btn_cancel: "Cancel",
      opt_anim_bouncy: "Bouncy Spring",
      opt_anim_neon: "Neon Glow Pulse",
      opt_anim_flash: "Color Flash Cycle",
      opt_anim_reveal: "Progressive Word Reveal",
      opt_anim_box: "Box Badge Highlight",
      opt_anim_classic: "Classic Subtitle Line",
      opt_words_2: "2 Words (Fast Pacing)",
      opt_words_3: "3 Words (Optimal Pacing)",
      opt_words_4: "4 Words",
      opt_words_5: "5 Words",
      opt_aspect_916: "9:16 (Shorts / Reels / TikTok)",
      opt_aspect_169: "16:9 (Landscape / YouTube)",
      opt_aspect_11: "1:1 (Square)",
      opt_bg_green: "Green Screen (Chroma Key)",
      opt_bg_black: "Black Screen (Screen Blend)",
      opt_bg_blue: "Blue Screen",
      opt_bg_orig: "Original Video (Burn-In)",
      opt_bg_trans: "Transparent Alpha (WebM)",
      opt_bg_custom: "Custom Color",
      ctrl_sub_box: "Subtitle Box Background",
      opt_box_none: "None (Clean Text Outline)",
      opt_box_pill: "Pill Badge (Rounded)",
      opt_box_block: "Full Block Box",
      opt_box_shadow: "Deep Drop Shadow",
      ctrl_box_color: "Box Color & Opacity",
      btn_add_more: "+ Add",
      queue_title: "Batch Processing Queue",
      queue_badge: "BATCH QUEUE",
      queue_clear: "Clear Queue"
    },
    fr: {
      header_badge: "STUDIO",
      brand_tagline: "Sous-titres animés automatiques et simulation smartphone sécurisée",
      btn_guide: "Guide",
      studio_title: "Studio & Aperçu du Résultat",
      studio_subtitle: "GÉNÉRATEUR",
      dropzone_title: "Glissez votre fichier Audio ou Vidéo ici",
      dropzone_formats: "Prend en charge MP3, WAV, AAC, MP4, MOV, MKV, WebM",
      btn_browse: "Parcourir",
      progress_idle: "Prêt pour le traitement...",
      badge_synced: "100% Synchronisé",
      badge_shorts: "Shorts & Reels",
      badge_comic: "Style Néo-Comic",
      dl_video: "Vidéo (MP4)",
      dl_ass: "ASS Animé",
      dl_srt: "Fichier SRT",
      dl_json: "Horodatage JSON",
      dl_remotion: "Remotion (React)",
      empty_title: "Prêt à créer des sous-titres viraux",
      empty_desc: "Importez un fichier audio ou vidéo. L'IA transcrit la parole avec horodatage mot par mot et applique des sous-titres animés selon votre style.",
      editor_title: "Éditeur de mots & minutage",
      btn_rerender: "Re-rendre les modifs",
      customization_title: "Personnalisation des Sous-titres & Vidéo",
      customization_badge: "RÉGLAGES",
      sim_heading: "Simulation Smartphone",
      sim_safe_zone: "ZONE SÛRE",
      pos_quick: "Position :",
      pos_top: "Haut",
      pos_middle: "Milieu",
      pos_safe_bottom: "Bas sécurisé",
      presets_title: "Préréglages de Style Viraux",
      preset_gold: "Or TikTok",
      preset_cyan: "Cyber Cyan",
      preset_coral: "Corail Vif",
      preset_lime: "Citron Punch",
      preset_comic: "Comic Pop",
      preset_white: "Blanc Classique",
      ctrl_lang: "Langue du contenu",
      ctrl_pos: "Position des sous-titres",
      ctrl_margin: "Marge verticale",
      ctrl_font: "Police d'écriture",
      ctrl_fontsize: "Taille de police",
      ctrl_anim: "Style d'animation",
      ctrl_animspeed: "Vitesse d'animation",
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
      step_1: "1/4: Téléversement et analyse audio par l'IA...",
      step_2: "2/4: Mots et horodatages extraits ! Création des animations...",
      step_3: "3/4: Rendu de la vidéo animée avec FFmpeg...",
      step_4: "Terminé avec succès ! Visionnez et téléchargez ci-dessous.",
      alert_no_file: "Veuillez d'abord téléverser un fichier audio ou vidéo !",
      sim_tiktok_caption: "Gardez les sous-titres au-dessus de cette zone pour éviter tout masquage !",
      sim_reels_caption: "Gardez les sous-titres au-dessus de cette zone pour éviter tout masquage !",
      sim_shorts_caption: "Gardez les sous-titres au-dessus de cette zone pour éviter tout masquage !",
      sim_follow: "Suivre",
      sim_subscribe: "S'abonner",
      // Dropdown Options
      opt_lang_dz: "Darija algérienne (الدارجة الجزائرية)",
      opt_lang_latin: "Darija algérienne (Latin / Arabizi 3, 7, 9)",
      opt_lang_msa: "Arabe standard moderne (العربية الفصحى)",
      opt_lang_fr: "Français",
      opt_lang_en: "Anglais",
      opt_pos_bottom: "Bas (Zone sûre au-dessus de l'UI)",
      opt_pos_center: "Centre (Milieu)",
      opt_pos_top: "Haut (En-tête)",
      opt_anim_karaoke: "Karaoké Pop & Échelle",
      opt_anim_minimal: "Glissement fluide minimal",
      opt_anim_cyber: "Neon Cyberpunk vibrant",
      opt_anim_comic: "Rebond BD dynamique",
      opt_anim_punch: "Impact viral percutant",
      opt_anim_editorial: "Fondu fluide editorial",
      opt_anim_badge: "Badge inverse neon",
      btn_save_preset: "+ Enregistrer actuel",
      save_preset_title: "Enregistrer un Prereglage",
      save_preset_desc: "Enregistrez vos polices, couleurs, animation et position pour vos futures sessions sans connexion.",
      preset_name_label: "Nom du Prereglage",
      preset_name_placeholder: "ex. TikTok Viral, Shorts Gaming",
      btn_save: "Enregistrer",
      btn_cancel: "Annuler",
      opt_anim_bouncy: "Rebond Élastique",
      opt_anim_neon: "Halo Néon Brillant",
      opt_anim_flash: "Flash de Couleurs Alternées",
      opt_anim_reveal: "Révélation Progressive de Mots",
      opt_anim_box: "Surlignage en Boîte Badge",
      opt_anim_classic: "Ligne Classique de Sous-titres",
      opt_words_2: "2 Mots (Rythme Rapide)",
      opt_words_3: "3 Mots (Rythme Idéal)",
      opt_words_4: "4 Mots",
      opt_words_5: "5 Mots",
      opt_aspect_916: "9:16 (Shorts / Reels / TikTok)",
      opt_aspect_169: "16:9 (Paysage / YouTube)",
      opt_aspect_11: "1:1 (Carré)",
      opt_bg_green: "Fond Vert (Chroma Key)",
      opt_bg_black: "Fond Noir (Mode Fusion Écran)",
      opt_bg_blue: "Fond Bleu",
      opt_bg_orig: "Vidéo d'origine (Incrustation)",
      opt_bg_trans: "Alpha Transparent (WebM)",
      opt_bg_custom: "Couleur Personnalisée",
      ctrl_sub_box: "Boîte d'arrière-plan du texte",
      opt_box_none: "Aucun (Contour texte seul)",
      opt_box_pill: "Badge Pilule (Arrondi)",
      opt_box_block: "Bloc Plein",
      opt_box_shadow: "Ombre Portée Profonde",
      ctrl_box_color: "Couleur et Opacité de la Boîte",
      btn_add_more: "+ Ajouter",
      queue_title: "File de Traitement par Lot",
      queue_badge: "FILE D'ATTENTE",
      queue_clear: "Vider la file"
    },
    ar: {
      header_badge: "استوديو",
      brand_tagline: "توليد الترجمة التلقائية المتحركة ومحاكاة شاشات الهواتف ومناطق الأمان",
      btn_guide: "دليل الاستخدام",
      studio_title: "معاينة الاستوديو والنتيجة",
      studio_subtitle: "المولّد",
      dropzone_title: "اسحب ملف الصوت أو الفيديو هنا",
      dropzone_formats: "يدعم MP3، WAV، AAC، MP4، MOV، MKV، WebM",
      btn_browse: "استعراض الملفات",
      progress_idle: "جاهز لبدء المعالجة...",
      badge_synced: "100% متزامن",
      badge_shorts: "ريلز وشورتس",
      badge_comic: "ستايل كوميك",
      dl_video: "تحميل الفيديو (MP4)",
      dl_ass: "ملف ASS المتحرك",
      dl_srt: "ملف SRT",
      dl_json: "توقيتات JSON",
      dl_remotion: "ريموشن (React)",
      empty_title: "جاهز لتوليد ترجمات متحركة احترافية",
      empty_desc: "قم برفع ملف صوتي أو فيديو. سيقوم الذكاء الاصطناعي بتوليد الترجمة المتزامنة مع كل كلمة وتطبيق الأنيميشن مع كروما خضراء أو دمج مباشر.",
      editor_title: "محرر ومراجعة الكلمات والتوقيت",
      btn_rerender: "إعادة الرندر بالتعديلات",
      customization_title: "تخصيص وإعدادات الترجمة والفيديو",
      customization_badge: "التحكم",
      sim_heading: "محاكاة الهاتف",
      sim_safe_zone: "منطقة الأمان",
      pos_quick: "الموضع:",
      pos_top: "أعلى",
      pos_middle: "المنتصف",
      pos_safe_bottom: "أسفل آمن",
      presets_title: "أنماط جاهزة سريعة",
      preset_gold: "تيك توك ذهبي",
      preset_cyan: "سايبر سيان",
      preset_coral: "مرجاني ناري",
      preset_lime: "ليموني حيوي",
      preset_comic: "كوميك بوب",
      preset_white: "أبيض كلاسيكي",
      ctrl_lang: "لغة المحتوى الصوتي",
      ctrl_pos: "موضع الترجمة",
      ctrl_margin: "الهامش العمودي",
      ctrl_font: "نوع الخط",
      ctrl_fontsize: "حجم الخط",
      ctrl_anim: "نمط الأنيميشن (الحركة)",
      ctrl_animspeed: "سرعة ونعومة الأنيميشن",
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
      step_4: "اكتمل التوليد بنجاح! يمكنك الآن مشاهدة وتحميل النتيجة.",
      alert_no_file: "الرجاء رفع ملف صوتي أو فيديو أولاً!",
      sim_tiktok_caption: "احرص على أن تكون الترجمة فوق هذه المنطقة حتى لا تحجبها واجهة التطبيق!",
      sim_reels_caption: "احرص على أن تكون الترجمة فوق هذه المنطقة حتى لا تحجبها واجهة التطبيق!",
      sim_shorts_caption: "احرص على أن تكون الترجمة فوق هذه المنطقة حتى لا تحجبها واجهة التطبيق!",
      sim_follow: "متابعة",
      sim_subscribe: "اشتراك",
      // Dropdown Options
      opt_lang_dz: "الدارجة الجزائرية - عربي",
      opt_lang_latin: "الدارجة الجزائرية باللاتينية (عربيزي 3, 7, 9)",
      opt_lang_msa: "العربية الفصحى",
      opt_lang_fr: "الفرنسية (Français)",
      opt_lang_en: "الإنجليزية (English)",
      opt_pos_bottom: "أسفل (منطقة الأمان فوق واجهة التطبيق)",
      opt_pos_center: "الوسط (المنتصف)",
      opt_pos_top: "أعلى (الترويسة)",
      opt_anim_karaoke: "كاراوكي بوب وتكبير",
      opt_anim_minimal: "Glissement fluide minimal",
      opt_anim_cyber: "Neon Cyberpunk vibrant",
      opt_anim_comic: "Rebond BD dynamique",
      opt_anim_punch: "Impact viral percutant",
      opt_anim_editorial: "Fondu fluide editorial",
      opt_anim_badge: "Badge inverse neon",
      btn_save_preset: "+ حفظ الحالي",
      save_preset_title: "حفظ قالب مخصص",
      save_preset_desc: "احفظ خطك وألوانك وحركاتك وموضعك الحالي لجلساتك القادمة بكل سهولة وبدون أي تسجيل دخول.",
      preset_name_label: "اسم القالب",
      preset_name_placeholder: "مثال: تيك توك فيرال، شورتس ألعاب",
      btn_save: "حفظ القالب",
      btn_cancel: "إلغاء",
      opt_anim_bouncy: "قفز مرن نطاط",
      opt_anim_neon: "توهج نيون مضيء",
      opt_anim_flash: "وميض ألوان متبادلة",
      opt_anim_reveal: "كشف تدريجي للكلمات",
      opt_anim_box: "تسليط الضوء بمربع مميز",
      opt_anim_classic: "سطر الترجمة الكلاسيكي",
      opt_words_2: "كلمتان (إيقاع سريع)",
      opt_words_3: "3 كلمات (إيقاع متوازن)",
      opt_words_4: "4 كلمات",
      opt_words_5: "5 كلمات",
      opt_aspect_916: "9:16 (شورتس / ريلز / تيك توك)",
      opt_aspect_169: "16:9 (أفقي / يوتيوب)",
      opt_aspect_11: "1:1 (مربع)",
      opt_bg_green: "شاشة خضراء (كروما كاي)",
      opt_bg_black: "شاشة سوداء (دمج الشاشة)",
      opt_bg_blue: "شاشة زرقاء",
      opt_bg_orig: "الفيديو الأصلي (حرق مباشر)",
      opt_bg_trans: "خلفية شفافة (WebM)",
      opt_bg_custom: "لون مخصص",
      ctrl_sub_box: "خلفية مربع الترجمة",
      opt_box_none: "بدون خلفية (تحديد النص فقط)",
      opt_box_pill: "شارة كبسولة دائرية (Pill)",
      opt_box_block: "مستطيل ممتلئ",
      opt_box_shadow: "ظل عميق بارز",
      ctrl_box_color: "لون وشفافية الخلفية",
      btn_add_more: "+ إضافة المزيد",
      queue_title: "قائمة المعالجة المتعددة",
      queue_badge: "قائمة الملفات",
      queue_clear: "إفراغ القائمة"
    }
  };

  // APPLY MULTILINGUAL FUNCTION
  function applyLanguage(lang) {
    if (!TRANSLATIONS[lang]) lang = "en";
    currentLang = lang;
    localStorage.setItem("dz_subtitles_lang", lang);

    document.documentElement.lang = lang;
    document.documentElement.dir = (lang === "ar") ? "rtl" : "ltr";

    langButtons.forEach(btn => {
      btn.classList.toggle("active", btn.dataset.lang === lang);
    });

    const dict = TRANSLATIONS[lang];

    // 1. Translate elements with data-i18n
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      if (dict[key]) {
        el.innerHTML = dict[key];
      }
    });

    // 2. Re-render Phone Simulator elements in the selected language
    updatePhonePlatformUI();

    // 3. Synchronize custom comic dropdown options and triggers
    if (typeof syncAllCustomDropdowns === "function") {
      syncAllCustomDropdowns();
    }
  }

  // Language button listeners
  langButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      applyLanguage(btn.dataset.lang);
    });
  });

  // THEME MANAGEMENT (Defaults to Dark Mode!)
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

  // -------------------------------------------------------------
  // CONFIGURATION STATE & PERSISTENT PRESET ENGINE
  // -------------------------------------------------------------
  const presetPillsGrid = document.getElementById("presetPillsGrid");
  const savePresetBtn = document.getElementById("savePresetBtn");
  const savePresetModal = document.getElementById("savePresetModal");
  const closeSavePresetBtn = document.getElementById("closeSavePresetBtn");
  const cancelSavePresetBtn = document.getElementById("cancelSavePresetBtn");
  const confirmSavePresetBtn = document.getElementById("confirmSavePresetBtn");
  const presetNameInput = document.getElementById("presetNameInput");
  const summaryFontPill = document.getElementById("summaryFontPill");
  const summaryAnimPill = document.getElementById("summaryAnimPill");
  const summaryPrimaryDot = document.getElementById("summaryPrimaryDot");
  const summaryHighlightDot = document.getElementById("summaryHighlightDot");

  let customPresets = [];
  try {
    const rawCustom = localStorage.getItem("dz_subtitles_custom_presets");
    if (rawCustom) customPresets = JSON.parse(rawCustom);
  } catch (e) {
    customPresets = [];
  }

  // Sync custom presets with backend server (zero-auth persistence)
  async function fetchServerPresets() {
    try {
      const res = await fetch("/api/presets");
      if (res.ok) {
        const srv = await res.json();
        if (Array.isArray(srv) && srv.length > 0) {
          const idMap = new Map();
          customPresets.forEach(p => idMap.set(p.id, p));
          srv.forEach(p => idMap.set(p.id, p));
          customPresets = Array.from(idMap.values());
          localStorage.setItem("dz_subtitles_custom_presets", JSON.stringify(customPresets));
          renderCustomPresets();
        }
      }
    } catch (e) {}
  }
  fetchServerPresets();

  function syncPresetsToDisk() {
    try {
      localStorage.setItem("dz_subtitles_custom_presets", JSON.stringify(customPresets));
      fetch("/api/presets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(customPresets)
      }).catch(() => {});
    } catch (e) {}
  }

  function getCurrentSettings() {
    return {
      font: fontName ? fontName.value : "Lalezar",
      fontSize: fontSize ? (parseInt(fontSize.value) || 56) : 56,
      primary: primaryColor ? primaryColor.value : "#FFFFFF",
      highlight: highlightColor ? highlightColor.value : "#FFE600",
      anim: animationStyle ? animationStyle.value : "karaoke_pop",
      speed: animSpeed ? (parseFloat(animSpeed.value) || 1.0) : 1.0,
      margin: marginV ? (parseInt(marginV.value) || 420) : 420,
      wordsPerLine: wordsPerLine ? (parseInt(wordsPerLine.value) || 3) : 3,
      alignment: alignment ? (parseInt(alignment.value) || 2) : 2,
      dialect: dialectHint ? dialectHint.value : "General Algerian",
      aspectRatio: aspectRatio ? aspectRatio.value : "9:16",
      backgroundMode: backgroundMode ? backgroundMode.value : "original_video",
      customColorHex: customColorHex ? customColorHex.value : "#1A1A24",
      subBoxStyle: subBoxStyle ? subBoxStyle.value : "none",
      subBoxColor: subBoxColor ? subBoxColor.value : "#000000",
      subBoxAlpha: subBoxAlpha ? (parseFloat(subBoxAlpha.value) || 0.85) : 0.85,
    };
  }

  function applySettings(s) {
    if (!s) return;
    if (s.font && fontName) fontName.value = s.font;
    if (s.fontSize && fontSize) {
      fontSize.value = s.fontSize;
      if (fontSizeVal) fontSizeVal.innerText = s.fontSize + "px";
    }
    if (s.primary && primaryColor) {
      primaryColor.value = s.primary;
      if (primaryColorText) primaryColorText.innerText = s.primary.toUpperCase();
    }
    if (s.highlight && highlightColor) {
      highlightColor.value = s.highlight;
      if (highlightColorText) highlightColorText.innerText = s.highlight.toUpperCase();
    }
    if (s.anim && animationStyle) animationStyle.value = s.anim;
    if (s.speed && animSpeed) {
      animSpeed.value = s.speed;
      updateAnimationSpeed(s.speed);
    }
    if (s.margin && marginV) {
      marginV.value = s.margin;
      if (marginVVal) marginVVal.innerText = s.margin + "px";
    }
    if (s.wordsPerLine && wordsPerLine) wordsPerLine.value = s.wordsPerLine;
    if (s.alignment && alignment) alignment.value = s.alignment;
    if (s.dialect && dialectHint) dialectHint.value = s.dialect;
    if (s.aspectRatio && aspectRatio) aspectRatio.value = s.aspectRatio;
    if (s.backgroundMode && backgroundMode) {
      backgroundMode.value = s.backgroundMode;
      if (customColorGroup) customColorGroup.style.display = (s.backgroundMode === "custom") ? "flex" : "none";
    }
    if (s.customColorHex && customColorHex) {
      customColorHex.value = s.customColorHex;
      if (customColorText) customColorText.innerText = s.customColorHex.toUpperCase();
    }
    if (s.subBoxStyle && subBoxStyle) subBoxStyle.value = s.subBoxStyle;
    if (s.subBoxColor && subBoxColor) {
      subBoxColor.value = s.subBoxColor;
      if (subBoxColorText) subBoxColorText.innerText = s.subBoxColor.toUpperCase();
    }
    if (s.subBoxAlpha && subBoxAlpha) {
      subBoxAlpha.value = s.subBoxAlpha;
      if (subBoxAlphaVal) subBoxAlphaVal.innerText = Math.round(parseFloat(s.subBoxAlpha) * 100) + "%";
    }

    updateLiveSubtitlePreview();
    syncAllCustomDropdowns();
    autoSaveSettings();
  }

  function autoSaveSettings() {
    try {
      const s = getCurrentSettings();
      localStorage.setItem("dz_subtitles_last_settings", JSON.stringify(s));
    } catch (e) {}
  }

  function restoreLastSettings() {
    try {
      const raw = localStorage.getItem("dz_subtitles_last_settings");
      if (raw) {
        const s = JSON.parse(raw);
        applySettings(s);
      }
    } catch (e) {}
  }

  // Render Custom Presets into Preset Pill Grid
  function renderCustomPresets() {
    if (!presetPillsGrid) return;
    presetPillsGrid.querySelectorAll(".comic-preset-btn.is-custom").forEach(el => el.remove());

    customPresets.forEach(p => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "comic-preset-btn is-custom";
      btn.dataset.presetId = p.id;
      btn.title = `Custom Preset: ${p.name}`;

      const dot = document.createElement("span");
      dot.className = "preset-dot";
      dot.style.background = p.highlight || "#FFE600";
      dot.style.borderColor = p.primary || "#000000";

      const label = document.createElement("span");
      label.innerText = p.name;

      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.className = "preset-remove-btn";
      delBtn.innerHTML = "&times;";
      delBtn.title = "Delete Preset";

      delBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (confirm(`Delete preset "${p.name}"?`)) {
          customPresets = customPresets.filter(item => item.id !== p.id);
          syncPresetsToDisk();
          renderCustomPresets();
        }
      });

      btn.appendChild(dot);
      btn.appendChild(label);
      btn.appendChild(delBtn);

      btn.addEventListener("click", () => {
        presetPillsGrid.querySelectorAll(".comic-preset-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        applySettings(p);
      });

      presetPillsGrid.appendChild(btn);
    });
  }

  // Modal event listeners
  if (savePresetBtn && savePresetModal) {
    savePresetBtn.addEventListener("click", () => {
      const s = getCurrentSettings();
      if (summaryFontPill) summaryFontPill.innerText = `${s.font} (${s.fontSize}px)`;
      if (summaryAnimPill) summaryAnimPill.innerText = s.anim.replace(/_/g, " ").replace(/-/g, " ");
      if (summaryPrimaryDot) summaryPrimaryDot.style.background = s.primary;
      if (summaryHighlightDot) summaryHighlightDot.style.background = s.highlight;
      if (presetNameInput) {
        presetNameInput.value = "";
        setTimeout(() => presetNameInput.focus(), 100);
      }
      savePresetModal.classList.remove("hidden");
    });
  }

  if (closeSavePresetBtn && savePresetModal) {
    closeSavePresetBtn.addEventListener("click", () => savePresetModal.classList.add("hidden"));
  }
  if (cancelSavePresetBtn && savePresetModal) {
    cancelSavePresetBtn.addEventListener("click", () => savePresetModal.classList.add("hidden"));
  }
  if (savePresetModal) {
    savePresetModal.addEventListener("click", (e) => {
      if (e.target === savePresetModal) savePresetModal.classList.add("hidden");
    });
  }

  if (confirmSavePresetBtn) {
    confirmSavePresetBtn.addEventListener("click", () => {
      const name = (presetNameInput && presetNameInput.value.trim()) || `Preset ${customPresets.length + 1}`;
      const s = getCurrentSettings();
      const newPreset = {
        id: "preset_" + Date.now(),
        name,
        ...s,
        createdAt: Date.now()
      };
      customPresets.push(newPreset);
      syncPresetsToDisk();
      renderCustomPresets();
      if (savePresetModal) savePresetModal.classList.add("hidden");

      setTimeout(() => {
        const newBtn = presetPillsGrid.querySelector(`[data-preset-id="${newPreset.id}"]`);
        if (newBtn) {
          presetPillsGrid.querySelectorAll(".comic-preset-btn").forEach(b => b.classList.remove("active"));
          newBtn.classList.add("active");
        }
      }, 50);
    });
  }

  window.addEventListener("beforeunload", autoSaveSettings);

  // STYLE PRESETS (Built-in)
  const PRESETS = {
    gold: { primary: "#FFFFFF", highlight: "#FFE600", font: "Lalezar", anim: "karaoke_pop", align: "2", margin: 420 },
    cyan: { primary: "#FFFFFF", highlight: "#00F0FF", font: "Tajawal", anim: "karaoke_pop", align: "2", margin: 420 },
    coral: { primary: "#FFFFFF", highlight: "#FF8A00", font: "Lalezar", anim: "bouncy_spring", align: "2", margin: 420 },
    lime: { primary: "#FFFFFF", highlight: "#00FF9D", font: "Almarai", anim: "karaoke_pop", align: "2", margin: 420 },
    comic: { primary: "#FFFFFF", highlight: "#FFE600", font: "Lalezar", anim: "box_highlight", align: "2", margin: 420 },
    white: { primary: "#FFFFFF", highlight: "#FFE600", font: "Cairo", anim: "classic_line", align: "2", margin: 420 }
  };

  presetButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      if (presetPillsGrid) {
        presetPillsGrid.querySelectorAll(".comic-preset-btn").forEach(b => b.classList.remove("active"));
      }
      btn.classList.add("active");
      const p = PRESETS[btn.dataset.preset];
      if (p) {
        applySettings({
          ...getCurrentSettings(),
          primary: p.primary,
          highlight: p.highlight,
          font: p.font,
          anim: p.anim,
          alignment: p.align,
          margin: p.margin
        });
      }
    });
  });

  // PHONE PLATFORM TABS (TikTok / Reels / YouTube Shorts)
  platformTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      platformTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      currentPlatform = tab.dataset.platform;
      updatePhonePlatformUI();
    });
  });

  // DYNAMIC PHONE SIMULATION ENGINE (Accurately renders UI for TikTok, Reels, and YouTube Shorts)
  function updatePhonePlatformUI() {
    if (!platformTopBar || !phoneSidebar || !phoneBottomOverlay) return;
    const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;

    if (currentPlatform === "tiktok") {
      // 1. TikTok Top Nav
      platformTopBar.innerHTML = `
        <div class="tiktok-top-nav">
          <span class="top-nav-link">Live</span>
          <span class="top-nav-link">Following</span>
          <span class="top-nav-link active">For You</span>
          <svg class="top-nav-search" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        </div>`;

      // 2. TikTok Sidebar
      phoneSidebar.innerHTML = `
        <div class="side-item avatar-wrap">
          <div class="side-avatar"></div>
          <div class="follow-badge">+</div>
        </div>
        <div class="side-item">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="#ff2e56"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
          <span>142K</span>
        </div>
        <div class="side-item">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
          <span>2.3K</span>
        </div>
        <div class="side-item">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>
          <span>9.8K</span>
        </div>
        <div class="side-item">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
          <span>18K</span>
        </div>
`;

      // 3. TikTok Bottom Overlay
      phoneBottomOverlay.innerHTML = `
        <div class="creator-row">
          <span class="creator-tag">@creator_pro</span>
          <button type="button" class="btn-sub-badge">${dict.sim_follow}</button>
        </div>
        <p class="creator-desc">${dict.sim_tiktok_caption}</p>
        <div class="creator-sound">
          <svg width="9" height="9" viewBox="0 0 24 24" fill="currentColor"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>
          <span>Trending AI Voice • Original Audio</span>
        </div>
        <div class="phone-seekbar"></div>`;

    } else if (currentPlatform === "reels") {
      // 1. Instagram Reels Top Nav
      platformTopBar.innerHTML = `
        <div class="reels-top-nav" style="justify-content: space-between;">
          <span style="font-weight: 900; font-size: 11px; color: #fff;">Reels</span>
          <div style="display: flex; gap: 6px;">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
          </div>
        </div>`;

      // 2. Instagram Reels Sidebar
      phoneSidebar.innerHTML = `
        <div class="side-item">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
          <span>95.4K</span>
        </div>
        <div class="side-item">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
          <span>1.8K</span>
        </div>
        <div class="side-item">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
          <span>12K</span>
        </div>
        <div class="side-item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="5" r="2"></circle><circle cx="12" cy="12" r="2"></circle><circle cx="12" cy="19" r="2"></circle></svg>
        </div>
        <div class="side-item" style="margin-top: 4px;">
          <div style="width: 16px; height: 16px; border: 1.5px solid #fff; border-radius: 4px; background: #222;"></div>
        </div>`;

      // 3. Instagram Reels Bottom Overlay
      phoneBottomOverlay.innerHTML = `
        <div class="creator-row">
          <div style="width: 14px; height: 14px; border-radius: 50%; border: 1px solid #fff; background: var(--amber);"></div>
          <span class="creator-tag">@creator_pro</span>
          <button type="button" class="btn-sub-badge" style="background: transparent; border: 1px solid #fff;">${dict.sim_follow}</button>
        </div>
        <p class="creator-desc">${dict.sim_reels_caption}</p>
        <div class="creator-sound">
          <svg width="9" height="9" viewBox="0 0 24 24" fill="currentColor"><path d="M9 18V5l12-2v13"></path></svg>
          <span>original_audio • creator_pro</span>
        </div>`;

    } else if (currentPlatform === "shorts") {
      // 1. YouTube Shorts Top Nav
      platformTopBar.innerHTML = `
        <div class="shorts-top-nav" style="justify-content: space-between;">
          <span style="font-weight: 900; font-size: 11px; color: #fff; display: flex; align-items: center; gap: 4px;">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="#ff0000"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
            Shorts
          </span>
          <div style="display: flex; gap: 6px; align-items: center;">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="5" r="2"></circle><circle cx="12" cy="12" r="2"></circle><circle cx="12" cy="19" r="2"></circle></svg>
          </div>
        </div>`;

      // 2. YouTube Shorts Sidebar
      phoneSidebar.innerHTML = `
        <div class="side-item">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>
          <span>84K</span>
        </div>
        <div class="side-item">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"></path></svg>
          <span>Dislike</span>
        </div>
        <div class="side-item">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
          <span>3.1K</span>
        </div>
        <div class="side-item">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
          <span>Share</span>
        </div>
        <div class="side-item">
          <div style="width: 16px; height: 16px; border: 1.5px solid #fff; border-radius: 4px; background: #222; display: flex; align-items: center; justify-content: center; font-size: 8px; font-weight: 900;">R</div>
          <span>Remix</span>
        </div>`;

      // 3. YouTube Shorts Bottom Overlay
      phoneBottomOverlay.innerHTML = `
        <div class="creator-row">
          <div style="width: 14px; height: 14px; border-radius: 50%; border: 1px solid #fff; background: var(--terracotta);"></div>
          <span class="creator-tag">@creator_pro</span>
          <button type="button" class="btn-sub-badge" style="background: #ffffff; color: #000; font-weight: 900; border-radius: 999px;">${dict.sim_subscribe}</button>
        </div>
        <p class="creator-desc">${dict.sim_shorts_caption}</p>
        <div class="creator-sound">
          <svg width="9" height="9" viewBox="0 0 24 24" fill="currentColor"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
          <span>Shorts Audio Library</span>
        </div>`;
    }
  }

  // LIVE SUBTITLE PREVIEW IN PHONE SIMULATOR
  // LIVE SUBTITLE PREVIEW IN PHONE SIMULATION
  let previewActiveIdx = 1;
  let previewCycleTimer = null;

  function updateLiveSubtitlePreview() {
    if (!liveSubtitleContainer || !liveSubtitleBox) return;

    // Font styling (supports Lalezar, Cairo, Tajawal, Almarai, Amiri, etc.)
    liveSubtitleBox.style.fontFamily = fontName.value + ", sans-serif";
    const scaledSize = Math.max(9, Math.round(parseInt(fontSize.value) * 0.18));
    liveSubtitleBox.style.fontSize = scaledSize + "px";

    // Set sample words adapted to selected dialect when no user media has been transcribed yet
    if (!currentTranscription) {
      if (dialectHint.value.includes("Latin")) {
        subWord1.innerText = "es-sayara";
        subWord2.innerText = "ta3i";
        subWord3.innerText = "echekhsiya";
      } else if (dialectHint.value === "French") {
        subWord1.innerText = "SOUS-TITRES";
        subWord2.innerText = "ANIMÉS";
        subWord3.innerText = "VIRAUX";
      } else if (dialectHint.value === "English") {
        subWord1.innerText = "VIRAL";
        subWord2.innerText = "ANIMATED";
        subWord3.innerText = "CAPTIONS";
      } else {
        // Default Algerian Darija (Arabic script)
        subWord1.innerText = "السيارة";
        subWord2.innerText = "تاعي";
        subWord3.innerText = "الشخصية";
      }
    }

    // RTL Detection: Ensure Arabic / Algerian Darija words are strictly RTL in the flex container
    const sampleText = (subWord1.innerText || "") + (subWord2.innerText || "") + (subWord3.innerText || "");
    const isArabic = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]/.test(sampleText) || 
                     (dialectHint.value.includes("Algerian") && !dialectHint.value.includes("Latin")) || 
                     dialectHint.value.includes("Arabic");

    if (isArabic) {
      liveSubtitleBox.setAttribute("dir", "rtl");
      liveSubtitleBox.classList.remove("is-ltr");
      liveSubtitleBox.classList.add("is-rtl");
    } else {
      liveSubtitleBox.setAttribute("dir", "ltr");
      liveSubtitleBox.classList.remove("is-rtl");
      liveSubtitleBox.classList.add("is-ltr");
    }

    // Subtitle Background Box Styling
    const boxStyle = subBoxStyle ? subBoxStyle.value : "none";
    liveSubtitleBox.setAttribute("data-box-style", boxStyle);
    if (subBoxControls) {
      subBoxControls.style.display = (boxStyle === "none") ? "none" : "block";
    }

    if (boxStyle !== "none" && subBoxColor && subBoxAlpha) {
      const hex = subBoxColor.value;
      const r = parseInt(hex.slice(1, 3), 16) || 0;
      const g = parseInt(hex.slice(3, 5), 16) || 0;
      const b = parseInt(hex.slice(5, 7), 16) || 0;
      const a = parseFloat(subBoxAlpha.value) || 0.85;
      liveSubtitleBox.style.setProperty("--sub-box-bg", `rgba(${r}, ${g}, ${b}, ${a})`);
      liveSubtitleBox.style.setProperty("--sub-box-color", hex);
    } else {
      liveSubtitleBox.style.removeProperty("--sub-box-bg");
      liveSubtitleBox.style.removeProperty("--sub-box-color");
    }

    // Apply animation style & active word colors
    const activeAnim = animationStyle.value || "karaoke_pop";
    const words = [subWord1, subWord2, subWord3];

    // Ensure CSS highlight preview color is kept in sync
    document.documentElement.style.setProperty("--highlight-preview", highlightColor.value);

    words.forEach((w, idx) => {
      if (!w) return;

      // BiDi Loanword Isolation: In an RTL context, wrap or flag Latin tokens with dir="ltr" and .bidi-isolate
      const wordText = w.innerText || "";
      const isLatin = /[a-zA-Z]/.test(wordText);
      const bidiClass = (isArabic && isLatin) ? " bidi-isolate" : "";
      if (isArabic && isLatin) {
        w.setAttribute("dir", "ltr");
        w.style.unicodeBidi = "isolate";
      } else {
        w.removeAttribute("dir");
        w.style.unicodeBidi = "";
      }

      if (idx === previewActiveIdx) {
        // Trigger reflow to restart CSS animation from frame 0 for clean opening ease
        w.style.animation = "none";
        void w.offsetWidth;
        w.style.animation = "";

        w.className = `sub-word active anim-${activeAnim}${bidiClass}`;
        if (activeAnim === "box_highlight" || activeAnim === "badge_invert") {
          w.style.background = highlightColor.value;
          w.style.color = "#000000";
          w.style.padding = "1px 6px";
          w.style.borderRadius = "4px";
        } else {
          w.style.background = "none";
          w.style.color = highlightColor.value;
          w.style.padding = "0";
        }
      } else {
        w.className = `sub-word${bidiClass}`;
        w.style.background = "none";
        w.style.color = primaryColor.value;
        w.style.padding = "0";
      }
    });

    // Position mapping inside simulated phone (based on marginV)
    const marginPixels = parseInt(marginV.value) || 420;
    const topPct = Math.max(10, Math.min(88, (1 - (marginPixels / 1920)) * 100));
    
    // Only set style if not currently dragging by pointer
    if (!isDraggingSubtitle) {
      liveSubtitleContainer.style.top = topPct + "%";
      liveSubtitleContainer.style.bottom = "auto";
      liveSubtitleContainer.style.transform = "translateX(-50%)";
    }
  }

  // Fluid preview cycle timer: rhythmic word-by-word karaoke progression on the phone screen
  function restartPreviewCycle() {
    if (previewCycleTimer) clearInterval(previewCycleTimer);
    const speed = parseFloat(animSpeed ? animSpeed.value : 1.0) || 1.0;
    const intervalMs = Math.max(450, Math.round(1150 / speed));
    previewCycleTimer = setInterval(stepPreviewCycle, intervalMs);
  }

  function stepPreviewCycle() {
    previewActiveIdx = (previewActiveIdx + 1) % 3;
    updateLiveSubtitlePreview();
  }

  restartPreviewCycle();

  // DRAGGABLE SUBTITLES ON PHONE SIMULATION (Direct mouse / touch dragging!)
  let isDraggingSubtitle = false;

  function handleDragStart(e) {
    if (!phoneDevice || !liveSubtitleContainer) return;
    isDraggingSubtitle = true;
    liveSubtitleContainer.classList.add("is-dragging");
    if (dragTooltip) dragTooltip.classList.remove("hidden");
    e.preventDefault();
  }

  function handleDragMove(e) {
    if (!isDraggingSubtitle || !phoneDevice || !liveSubtitleContainer) return;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    const rect = phoneDevice.getBoundingClientRect();
    const offsetY = clientY - rect.top;
    let pct = (offsetY / rect.height) * 100;
    // Constrain inside phone screen safe zones (10% to 86%)
    pct = Math.max(10, Math.min(86, pct));

    liveSubtitleContainer.style.top = pct + "%";
    liveSubtitleContainer.style.bottom = "auto";
    liveSubtitleContainer.style.transform = "translateX(-50%)";

    // Calibrate corresponding MarginV for 1920px vertical resolution
    const calculatedMarginV = Math.round((1 - (pct / 100)) * 1920);
    marginV.value = calculatedMarginV;

    let zoneLabel = "Custom";
    if (pct >= 62 && pct <= 80) {
      zoneLabel = "Safe Zone";
    } else if (pct < 30) {
      zoneLabel = "Top Header";
    } else {
      zoneLabel = "Middle";
    }

    if (dragTooltip) {
      dragTooltip.innerText = `${zoneLabel} (${Math.round(pct)}% Y • ${calculatedMarginV}px)`;
    }
    marginVVal.innerText = `${calculatedMarginV}px (${zoneLabel})`;
  }

  function handleDragEnd() {
    if (!isDraggingSubtitle) return;
    isDraggingSubtitle = false;
    liveSubtitleContainer.classList.remove("is-dragging");
    if (dragTooltip) dragTooltip.classList.add("hidden");
  }

  liveSubtitleContainer.addEventListener("mousedown", handleDragStart);
  window.addEventListener("mousemove", handleDragMove);
  window.addEventListener("mouseup", handleDragEnd);

  liveSubtitleContainer.addEventListener("touchstart", handleDragStart, { passive: false });
  window.addEventListener("touchmove", handleDragMove, { passive: false });
  window.addEventListener("touchend", handleDragEnd);

  // MarginV slider listener
  marginV.addEventListener("input", (e) => {
    const val = parseInt(e.target.value);
    const pct = Math.max(10, Math.min(86, (1 - (val / 1920)) * 100));
    liveSubtitleContainer.style.top = pct + "%";
    let zone = "Custom";
    if (pct >= 62 && pct <= 80) zone = "Safe Zone";
    else if (pct < 30) zone = "Top Header";
    else zone = "Middle";
    marginVVal.innerText = `${val}px (${zone})`;
  });

  // CUSTOM ANIMATED SELECT DROPDOWN LOGIC
  if (animSelectTrigger && animDropdownPanel) {
    animSelectTrigger.addEventListener("click", (e) => {
      e.stopPropagation();
      animDropdownPanel.classList.toggle("hidden");
      const chevron = animSelectTrigger.querySelector(".trigger-chevron");
      if (chevron) {
        chevron.style.transform = animDropdownPanel.classList.contains("hidden") ? "rotate(0deg)" : "rotate(180deg)";
      }
    });

    animOptionRows.forEach(row => {
      row.addEventListener("click", (e) => {
        e.stopPropagation();
        const val = row.dataset.value;
        animationStyle.value = val;
        animOptionRows.forEach(r => r.classList.remove("active"));
        row.classList.add("active");

        const nameEl = row.querySelector(".opt-name");
        const demoEl = row.querySelector(".opt-demo-box");
        if (nameEl && animSelectLabel) animSelectLabel.innerText = nameEl.innerText;
        if (demoEl && animSelectLivePreview) animSelectLivePreview.innerHTML = demoEl.innerHTML;

        animDropdownPanel.classList.add("hidden");
        const chevron = animSelectTrigger.querySelector(".trigger-chevron");
        if (chevron) chevron.style.transform = "rotate(0deg)";

        updateLiveSubtitlePreview();
        syncAllCustomDropdowns();
      });
    });

    document.addEventListener("click", (e) => {
      if (!animSelectWrap.contains(e.target)) {
        animDropdownPanel.classList.add("hidden");
        const chevron = animSelectTrigger.querySelector(".trigger-chevron");
        if (chevron) chevron.style.transform = "rotate(0deg)";
      }
    });
  }

  // UNIVERSAL CUSTOM RETRO-COMIC DROPDOWN ENGINE
  function enhanceSelectsToComicDropdowns() {
    const selectsToEnhance = [
      { el: dialectHint, type: "lang" },
      { el: fontName, type: "font" },
      { el: wordsPerLine, type: "words" },
      { el: aspectRatio, type: "aspect" },
      { el: subBoxStyle, type: "box" },
      { el: backgroundMode, type: "bg" }
    ];

    selectsToEnhance.forEach(({ el, type }) => {
      if (!el || el.dataset.enhanced === "true") return;
      el.dataset.enhanced = "true";
      el.classList.add("visually-hidden");

      const wrap = document.createElement("div");
      wrap.className = "custom-select-wrap comic-enhanced-select";
      wrap.dataset.selectId = el.id;

      const trigger = document.createElement("button");
      trigger.type = "button";
      trigger.className = "custom-select-trigger";
      trigger.setAttribute("aria-haspopup", "listbox");

      const left = document.createElement("div");
      left.className = "trigger-left";
      const labelSpan = document.createElement("span");
      labelSpan.className = "trigger-label";
      
      const selectedOpt = el.options[el.selectedIndex] || el.options[0];
      labelSpan.innerText = selectedOpt ? selectedOpt.innerText : "";
      if (type === "font" && selectedOpt) {
        labelSpan.style.fontFamily = selectedOpt.value + ", sans-serif";
      }
      left.appendChild(labelSpan);

      const chevron = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      chevron.setAttribute("class", "trigger-chevron");
      chevron.setAttribute("width", "14");
      chevron.setAttribute("height", "14");
      chevron.setAttribute("viewBox", "0 0 24 24");
      chevron.setAttribute("fill", "none");
      chevron.setAttribute("stroke", "currentColor");
      chevron.setAttribute("stroke-width", "2.5");
      chevron.innerHTML = '<polyline points="6 9 12 15 18 9"></polyline>';

      trigger.appendChild(left);
      trigger.appendChild(chevron);

      const panel = document.createElement("div");
      panel.className = "custom-dropdown-panel hidden";
      panel.setAttribute("role", "listbox");

      Array.from(el.options).forEach(opt => {
        const optRow = document.createElement("div");
        optRow.className = `comic-dropdown-option ${opt.selected ? 'active' : ''}`;
        optRow.dataset.value = opt.value;
        if (opt.getAttribute("data-i18n")) {
          optRow.setAttribute("data-i18n", opt.getAttribute("data-i18n"));
        }

        const textSpan = document.createElement("span");
        textSpan.innerText = opt.innerText;

        if (type === "font") {
          textSpan.style.fontFamily = opt.value + ", sans-serif";
          textSpan.style.fontSize = "12px";
          textSpan.style.letterSpacing = "0.5px";
        }

        optRow.appendChild(textSpan);

        if (type === "bg") {
          const badge = document.createElement("span");
          badge.className = "opt-badge";
          if (opt.value === "transparent") {
            badge.innerText = "ALPHA";
            badge.style.background = "var(--cyan)";
            badge.style.color = "#000";
          } else if (opt.value === "green_screen") {
            badge.innerText = "CHROMA";
            badge.style.background = "#00FF66";
            badge.style.color = "#000";
          } else if (opt.value === "black") {
            badge.innerText = "BLEND";
            badge.style.background = "#111";
            badge.style.color = "#fff";
          } else if (opt.value === "original_video") {
            badge.innerText = "OVERLAY";
            badge.style.background = "var(--terracotta)";
            badge.style.color = "#fff";
          } else if (opt.value === "custom") {
            badge.innerText = "HEX";
            badge.style.background = "var(--amber)";
            badge.style.color = "#000";
          }
          optRow.appendChild(badge);
        } else if (type === "lang") {
          if (opt.value.includes("Algerian") && !opt.value.includes("Latin")) {
            const badge = document.createElement("span");
            badge.className = "opt-badge";
            badge.innerText = "DEFAULT";
            badge.style.background = "var(--amber)";
            badge.style.color = "#000";
            optRow.appendChild(badge);
          } else if (opt.value.includes("Latin")) {
            const badge = document.createElement("span");
            badge.className = "opt-badge";
            badge.innerText = "3, 7, 9";
            badge.style.background = "var(--cyan)";
            badge.style.color = "#000";
            optRow.appendChild(badge);
          }
        }

        optRow.addEventListener("click", (e) => {
          e.stopPropagation();
          el.value = opt.value;
          panel.querySelectorAll(".comic-dropdown-option").forEach(r => r.classList.remove("active"));
          optRow.classList.add("active");
          labelSpan.innerText = opt.innerText;
          if (type === "font") {
            labelSpan.style.fontFamily = opt.value + ", sans-serif";
          }
          panel.classList.add("hidden");
          chevron.style.transform = "rotate(0deg)";

          el.dispatchEvent(new Event("change", { bubbles: true }));
          el.dispatchEvent(new Event("input", { bubbles: true }));
        });

        panel.appendChild(optRow);
      });

      trigger.addEventListener("click", (e) => {
        e.stopPropagation();
        document.querySelectorAll(".custom-dropdown-panel").forEach(p => {
          if (p !== panel) p.classList.add("hidden");
        });
        document.querySelectorAll(".trigger-chevron").forEach(c => {
          if (c !== chevron) c.style.transform = "rotate(0deg)";
        });

        panel.classList.toggle("hidden");
        chevron.style.transform = panel.classList.contains("hidden") ? "rotate(0deg)" : "rotate(180deg)";
      });

      wrap.appendChild(trigger);
      wrap.appendChild(panel);
      el.parentNode.insertBefore(wrap, el.nextSibling);
    });

    document.addEventListener("click", () => {
      document.querySelectorAll(".custom-dropdown-panel").forEach(p => p.classList.add("hidden"));
      document.querySelectorAll(".trigger-chevron").forEach(c => c.style.transform = "rotate(0deg)");
    });
  }

  function syncAllCustomDropdowns() {
    document.querySelectorAll(".comic-enhanced-select").forEach(wrap => {
      const selectId = wrap.dataset.selectId;
      const selectEl = document.getElementById(selectId);
      if (!selectEl) return;

      const label = wrap.querySelector(".trigger-label");
      const activeOpt = selectEl.options[selectEl.selectedIndex];
      if (label && activeOpt) {
        label.innerText = activeOpt.innerText;
        if (selectId === "fontName") {
          label.style.fontFamily = activeOpt.value + ", sans-serif";
        }
      }

      wrap.querySelectorAll(".comic-dropdown-option").forEach(optRow => {
        const val = optRow.dataset.value;
        const matchingOpt = Array.from(selectEl.options).find(o => o.value === val);
        if (matchingOpt) {
          const textSpan = optRow.querySelector("span:first-child");
          if (textSpan) textSpan.innerText = matchingOpt.innerText;
        }
        optRow.classList.toggle("active", val === selectEl.value);
      });
    });

    // Also sync anim dropdown label
    if (animSelectLabel && animationStyle) {
      const activeAnimRow = document.querySelector(`.anim-option-row[data-value="${animationStyle.value}"]`);
      if (activeAnimRow) {
        const nameEl = activeAnimRow.querySelector(".opt-name");
        const demoEl = activeAnimRow.querySelector(".opt-demo-box");
        if (nameEl) animSelectLabel.innerText = nameEl.innerText;
        if (demoEl && animSelectLivePreview) animSelectLivePreview.innerHTML = demoEl.innerHTML;
        document.querySelectorAll(".anim-option-row").forEach(r => r.classList.remove("active"));
        activeAnimRow.classList.add("active");
      }
    }
  }

  // Dialect change handler: update preview text and RTL direction
  dialectHint.addEventListener("change", () => {
    updateLiveSubtitlePreview();
    syncAllCustomDropdowns();
  });

  marginV.addEventListener("input", (e) => {
    marginVVal.innerText = e.target.value + "px";
    requestAnimationFrame(updateLiveSubtitlePreview);
  });

  fontSize.addEventListener("input", (e) => {
    fontSizeVal.innerText = e.target.value + "px";
    requestAnimationFrame(updateLiveSubtitlePreview);
  });

  // ANIMATION SPEED & FLUIDITY CONTROLS
  function updateAnimationSpeed(speedVal) {
    const val = parseFloat(speedVal) || 1.0;
    document.documentElement.style.setProperty("--anim-speed", val);
    document.documentElement.style.setProperty("--highlight-preview", highlightColor.value);

    let speedLabel = "Balanced";
    if (val <= 0.75) speedLabel = "Smooth";
    else if (val <= 1.15) speedLabel = "Snappy";
    else if (val <= 1.55) speedLabel = "Viral";
    else speedLabel = "Rapid";

    if (animSpeedVal) {
      animSpeedVal.innerText = `${val.toFixed(1)}x (${speedLabel})`;
    }

    speedChips.forEach(chip => {
      const chipSpeed = parseFloat(chip.dataset.speed);
      chip.classList.toggle("active", Math.abs(chipSpeed - val) < 0.15);
    });

    restartPreviewCycle();
  }

  if (animSpeed) {
    animSpeed.addEventListener("input", (e) => {
      updateAnimationSpeed(e.target.value);
    });
  }

  speedChips.forEach(chip => {
    chip.addEventListener("click", () => {
      if (animSpeed) {
        animSpeed.value = chip.dataset.speed;
        updateAnimationSpeed(chip.dataset.speed);
      }
    });
  });

  fontName.addEventListener("change", () => { updateLiveSubtitlePreview(); autoSaveSettings(); });
  animationStyle.addEventListener("change", () => {
    updateLiveSubtitlePreview();
    restartPreviewCycle();
    autoSaveSettings();
  });

  primaryColor.addEventListener("input", (e) => {
    primaryColorText.innerText = e.target.value.toUpperCase();
    updateLiveSubtitlePreview();
  });

  highlightColor.addEventListener("input", (e) => {
    highlightColorText.innerText = e.target.value.toUpperCase();
    updateLiveSubtitlePreview();
  });

  // QUICK COLOR SWATCH CLICKS
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

  // SUBTITLE BACKGROUND BOX LISTENERS
  if (subBoxStyle) {
    subBoxStyle.addEventListener("change", () => {
      updateLiveSubtitlePreview();
    });
  }
  if (subBoxColor) {
    subBoxColor.addEventListener("input", (e) => {
      if (subBoxColorText) subBoxColorText.innerText = e.target.value.toUpperCase();
      updateLiveSubtitlePreview();
    });
  }
  if (subBoxAlpha) {
    subBoxAlpha.addEventListener("input", (e) => {
      const pct = Math.round(parseFloat(e.target.value) * 100);
      if (subBoxAlphaVal) subBoxAlphaVal.innerText = `${pct}%`;
      updateLiveSubtitlePreview();
    });
  }

  // ADD MORE MEDIA BUTTONS
  if (addMoreFilesBtn) {
    addMoreFilesBtn.addEventListener("click", () => fileInput.click());
  }
  if (queueAddBtn) {
    queueAddBtn.addEventListener("click", () => fileInput.click());
  }

  // GUIDE MODAL TOGGLES
  guideBtn.addEventListener("click", () => guideModal.classList.remove("hidden"));
  closeGuideBtn.addEventListener("click", () => guideModal.classList.add("hidden"));
  guideModal.addEventListener("click", (e) => {
    if (e.target === guideModal) guideModal.classList.add("hidden");
  });

  // FILE UPLOAD AND DRAG-AND-DROP HANDLERS
  function setFile(file, fromQueue = false) {
    if (!file) return;
    currentFile = file;
    fileName.innerText = file.name;
    fileSize.innerText = (file.size / (1024 * 1024)).toFixed(2) + " MB";

    const isVideo = file.type.startsWith("video/") || /\.(mp4|mov|mkv|webm)$/i.test(file.name);
    fileIconSymbol.innerHTML = isVideo ? `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <rect x="2" y="2" width="20" height="20" rx="2.18"></rect>
        <line x1="7" y1="2" x2="7" y2="22"></line>
        <line x1="17" y1="2" x2="17" y2="22"></line>
        <line x1="2" y1="12" x2="22" y2="12"></line>
      </svg>` : `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <path d="M9 18V5l12-2v13"></path>
        <circle cx="6" cy="18" r="3"></circle>
        <circle cx="18" cy="16" r="3"></circle>
      </svg>`;

    if (isVideo) {
      backgroundMode.value = "original_video";
      if (phoneVideoBg) {
        phoneVideoBg.src = URL.createObjectURL(file);
        phoneVideoBg.style.display = "block";
        phoneVideoBg.play().catch(() => {});
      }
    } else {
      backgroundMode.value = "transparent";
      if (phoneVideoBg) {
        phoneVideoBg.src = "";
        phoneVideoBg.style.display = "none";
      }
    }
    backgroundMode.dispatchEvent(new Event("change"));
    if (typeof syncAllCustomDropdowns === "function") {
      syncAllCustomDropdowns();
    }

    // When items are in queue, keep top dropzone in clean upload button mode
    if (fromQueue || batchQueue.length > 0) {
      fileInfo.classList.add("hidden");
      document.querySelector(".dropzone-body").classList.remove("hidden");
    } else {
      fileInfo.classList.remove("hidden");
      document.querySelector(".dropzone-body").classList.add("hidden");
    }
  }

  // Remove single item from queue
  window.removeQueueItem = function(idx) {
    if (idx < 0 || idx >= batchQueue.length) return;
    const removed = batchQueue.splice(idx, 1)[0];
    if (currentFile === removed.file) {
      if (batchQueue.length > 0) {
        const nextIdx = Math.min(idx, batchQueue.length - 1);
        setFile(batchQueue[nextIdx].file, true);
        if (batchQueue[nextIdx].task_id) currentTaskId = batchQueue[nextIdx].task_id;
        if (batchQueue[nextIdx].transcription) currentTranscription = batchQueue[nextIdx].transcription;
      } else {
        clearFile();
      }
    }
    renderQueueList();
  };

  function clearFile() {
    currentFile = null;
    fileInput.value = "";
    if (phoneVideoBg) {
      phoneVideoBg.src = "";
      phoneVideoBg.style.display = "none";
    }
    fileInfo.classList.add("hidden");
    document.querySelector(".dropzone-body").classList.remove("hidden");
    if (typeof syncAllCustomDropdowns === "function") {
      syncAllCustomDropdowns();
    }
  }

  // BATCH QUEUE FUNCTIONS
  function renderQueueList() {
    if (!queueItemsList || !queueSection) return;
    if (batchQueue.length === 0) {
      queueSection.classList.add("hidden");
      return;
    }

    queueSection.classList.remove("hidden");
    if (queueCount) queueCount.innerText = `${batchQueue.length} ${batchQueue.length === 1 ? 'file' : 'files'}`;
    queueItemsList.innerHTML = "";

    batchQueue.forEach((item, idx) => {
      const qItem = document.createElement("div");
      qItem.className = `queue-item ${item.file === currentFile ? 'active' : ''} ${item.status === 'done' ? 'done' : ''}`;
      
      const isVid = item.file.type.startsWith("video/") || /\.(mp4|mov|mkv|webm)$/i.test(item.file.name);
      const iconSvg = isVid ? `
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <rect x="2" y="2" width="20" height="20" rx="2.18"></rect>
          <line x1="7" y1="2" x2="7" y2="22"></line>
        </svg>` : `
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M9 18V5l12-2v13"></path>
          <circle cx="6" cy="18" r="3"></circle>
        </svg>`;

      let statusBadgeClass = "chip-queued";
      let statusText = "Queued";
      if (item.status === "processing") {
        statusBadgeClass = "chip-processing";
        statusText = "Processing...";
      } else if (item.status === "done") {
        statusBadgeClass = "chip-done";
        statusText = "Ready";
      } else if (item.status === "error") {
        statusBadgeClass = "chip-error";
        statusText = "Error";
      }

      qItem.innerHTML = `
        <div style="display: flex; align-items: center; gap: 5px; flex: 1; overflow: hidden;">
          <span style="color: var(--amber);">${iconSvg}</span>
          <div class="queue-item-meta">
            <span class="queue-item-name" title="${item.file.name}">${item.file.name}</span>
            <span class="queue-item-sub">${(item.file.size / (1024 * 1024)).toFixed(2)} MB</span>
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 4px;">
          <span class="queue-status-chip ${statusBadgeClass}">${statusText}</span>
          ${item.result ? `<a href="${item.result.video_url}" download class="comic-tag comic-tag-amber" onclick="event.stopPropagation()" style="text-decoration:none; padding: 2px 5px; font-size: 8px; font-weight: 900; display: inline-flex; align-items: center; gap: 2px;" title="Download Video">⬇ MP4</a>` : ''}
          <button type="button" class="comic-btn-square queue-del-btn" title="Remove file" onclick="event.stopPropagation(); window.removeQueueItem(${idx});" style="width: 18px; height: 18px; padding: 0; min-width: 18px; display: inline-flex; align-items: center; justify-content: center;">
            <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
      `;

      qItem.addEventListener("click", () => {
        setFile(item.file, true);
        if (item.task_id) currentTaskId = item.task_id;
        if (item.transcription) currentTranscription = item.transcription;
        renderQueueList();
        if (item.result) {
          resultVideo.src = item.result.video_url;
          downloadVideoBtn.href = item.result.video_url;
          downloadAssBtn.href = item.result.ass_url;
          downloadSrtBtn.href = item.result.srt_url;
          downloadJsonBtn.href = item.result.json_url;
          if (downloadRemotionBtn) {
            downloadRemotionBtn.href = item.result.remotion_url || `/api/download/${item.task_id}/remotion_props.json`;
          }
          videoContainer.classList.remove("hidden");
          emptyState.classList.add("hidden");
          if (item.transcription) renderEditor(item.transcription);
        }
      });

      queueItemsList.appendChild(qItem);
    });
  }

  function handleBatchFiles(filesList) {
    if (!filesList || filesList.length === 0) return;
    const newItems = Array.from(filesList).map(f => ({
      file: f,
      status: "queued",
      result: null,
      transcription: null,
      task_id: null
    }));

    batchQueue.push(...newItems);
    if (!currentFile && batchQueue.length > 0) {
      setFile(batchQueue[0].file, true);
    }
    renderQueueList();
    // Keep top dropzone in clean upload button mode so user can easily add more files
    fileInfo.classList.add("hidden");
    document.querySelector(".dropzone-body").classList.remove("hidden");
  }

  if (clearQueueBtn) {
    clearQueueBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      batchQueue = [];
      renderQueueList();
      clearFile();
    });
  }

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleBatchFiles(e.target.files);
      fileInput.value = "";
    }
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
    if (e.dataTransfer.files.length > 0) {
      handleBatchFiles(e.dataTransfer.files);
    }
  });

  // SYNTHESIZED COMPLETION CHIME (WEB AUDIO API)
  function playCompletionChime() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const now = ctx.currentTime;

      // Note 1: C5 (523.25 Hz)
      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      osc1.type = "sine";
      osc1.frequency.setValueAtTime(523.25, now);
      gain1.gain.setValueAtTime(0.18, now);
      gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
      osc1.connect(gain1);
      gain1.connect(ctx.destination);
      osc1.start(now);
      osc1.stop(now + 0.35);

      // Note 2: G5 (783.99 Hz)
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.type = "sine";
      osc2.frequency.setValueAtTime(783.99, now + 0.12);
      gain2.gain.setValueAtTime(0.22, now + 0.12);
      gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.55);
      osc2.connect(gain2);
      gain2.connect(ctx.destination);
      osc2.start(now + 0.12);
      osc2.stop(now + 0.55);
    } catch (e) {
      console.log("Audio chime note skipped", e);
    }
  }

  // PROGRESS TRACKER HELPER
  function updateProgress(percent, stepText, message, etaText = "") {
    progressContainer.classList.remove("hidden");
    progressBar.style.width = percent + "%";
    progressPercentage.innerText = percent + "%";
    progressStepBadge.innerText = stepText;
    progressStatus.innerText = message;
    if (progressEta) {
      progressEta.innerText = etaText || (percent === 100 ? "Done!" : "Est. ~8s");
    }
  }

  // SUBTITLE EDITOR POPULATION
  function renderEditor(transcription) {
    segmentsList.innerHTML = "";
    if (!transcription || !transcription.segments || transcription.segments.length === 0) {
      editorContainer.classList.add("hidden");
      return;
    }

    // Update phone preview with actual transcription sample words!
    const firstWords = transcription.segments[0].words;
    if (firstWords && firstWords.length > 0) {
      subWord1.innerText = firstWords[0] ? firstWords[0].word : "";
      subWord2.innerText = firstWords[1] ? firstWords[1].word : "";
      subWord3.innerText = firstWords[2] ? firstWords[2].word : "";
      subWord2.style.display = firstWords[1] ? "inline-block" : "none";
      subWord3.style.display = firstWords[2] ? "inline-block" : "none";
      updateLiveSubtitlePreview();
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
      input.setAttribute("dir", "auto");
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

  // PROCESS SINGLE ITEM IN BATCH OR DIRECT
  async function processFileItem(item) {
    const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
    setFile(item.file);
    item.status = "processing";
    renderQueueList();

    emptyState.classList.add("hidden");
    videoContainer.classList.add("hidden");

    // Fast-path: If item has already been transcribed, re-render directly with current settings in ~1-2s!
    if (item.transcription && item.task_id) {
      currentTaskId = item.task_id;
      currentTranscription = item.transcription;
      updateProgress(65, "Step 2/4", dict.step_2, "Est. ~2s");
      renderEditor(currentTranscription);
      const renderRes = await triggerRender();
      item.result = renderRes;
      item.status = "done";
      renderQueueList();
      return;
    }

    // Step 1: Upload & Transcribe
    updateProgress(25, "Step 1/4", dict.step_1, "Est. ~8s");

    const formData = new FormData();
    formData.append("file", item.file);
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
    item.task_id = currentTaskId;
    item.transcription = currentTranscription;

    updateProgress(65, "Step 2/4", dict.step_2, "Est. ~3s");
    renderEditor(currentTranscription);

    // Step 2: Render Subtitles & Composite Video
    const renderRes = await triggerRender();
    item.result = renderRes;
    item.status = "done";
    renderQueueList();
  }

  // GENERATE SUBTITLES FLOW (With Batch Queue support!)
  startBtn.addEventListener("click", async () => {
    const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
    if (batchQueue.length === 0 && !currentFile) {
      alert(dict.alert_no_file);
      return;
    }

    // If single file uploaded directly without queue
    if (batchQueue.length === 0 && currentFile) {
      batchQueue.push({
        file: currentFile,
        status: "queued",
        result: null,
        transcription: currentTranscription,
        task_id: currentTaskId
      });
      renderQueueList();
    }

    // If all items are currently 'done', re-mark them to 'queued' so clicking Generate RE-GENERATES!
    const allDone = batchQueue.length > 0 && batchQueue.every(item => item.status === "done");
    if (allDone) {
      batchQueue.forEach(item => {
        item.status = "queued";
      });
      renderQueueList();
    }

    startBtn.disabled = true;
    isProcessingBatch = true;

    try {
      let idx = 0;
      while (idx < batchQueue.length) {
        const item = batchQueue[idx];
        if (item.status !== "done") {
          try {
            await processFileItem(item);
          } catch (itemErr) {
            console.error("Item processing failed", itemErr);
            item.status = "error";
            renderQueueList();
          }
        }
        idx++;
      }
    } finally {
      startBtn.disabled = false;
      isProcessingBatch = false;
    }
  });

  // RE-RENDER WITH EDITED SUBTITLES
  reRenderBtn.addEventListener("click", async () => {
    if (!currentTaskId || !currentTranscription) return;
    reRenderBtn.disabled = true;
    const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
    updateProgress(50, "Re-rendering", dict.step_3, "Est. ~4s");
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
    updateProgress(80, "Step 3/4", dict.step_3, "Est. ~3s");

    const renderPayload = {
      task_id: currentTaskId,
      transcription_data: currentTranscription,
      font_name: fontName.value,
      font_size: parseInt(fontSize.value),
      primary_color: primaryColor.value,
      highlight_color: highlightColor.value,
      outline_color: "#000000",
      shadow_color: "#000000",
      outline_width: 2.4,
      shadow_depth: 2.2,
      alignment: parseInt(alignment.value) || 2,
      margin_v: parseInt(marginV.value) || 420,
      pos_y: Math.max(30, 1920 - (parseInt(marginV.value) || 420)),
      words_per_line: parseInt(wordsPerLine.value) || 4,
      template_id: animationStyle.value || "karaoke_pop",
      animation_style: animationStyle.value || "karaoke_pop",
      animation_speed: parseFloat(animSpeed ? animSpeed.value : 1.0) || 1.0,
      sub_box_style: subBoxStyle ? subBoxStyle.value : "none",
      sub_box_color: subBoxColor ? subBoxColor.value : "#000000",
      sub_box_alpha: parseFloat(subBoxAlpha ? subBoxAlpha.value : 0.85) || 0.85,
      background_mode: backgroundMode.value || "transparent",
      custom_color_hex: customColorHex.value,
      aspect_ratio: aspectRatio.value || "9:16"
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
    updateProgress(100, "Step 4/4", dict.step_4, "Complete!");

    // Play synthesized bell chime!
    playCompletionChime();

    // Smoothly dismiss loading progress bar after 1.4s
    setTimeout(() => {
      progressContainer.classList.add("hidden");
    }, 1400);

    // Update Player & Download buttons
    resultVideo.src = data.video_url;
    downloadVideoBtn.href = data.video_url;
    downloadAssBtn.href = data.ass_url;
    downloadSrtBtn.href = data.srt_url;
    downloadJsonBtn.href = data.json_url || `/api/download/${currentTaskId}/transcript.json`;
    if (downloadRemotionBtn) {
      downloadRemotionBtn.href = data.remotion_url || `/api/download/${currentTaskId}/remotion_props.json`;
    }

    videoContainer.classList.remove("hidden");
    resultVideo.load();
    resultVideo.play().catch(() => {});

    return data;
  }

  // INITIAL SETUP CALLS
  enhanceSelectsToComicDropdowns();
  applyLanguage(currentLang);
  applyTheme(currentTheme);
  renderCustomPresets();
  restoreLastSettings();
  updatePhonePlatformUI();
  updateLiveSubtitlePreview();
  syncAllCustomDropdowns();
});
