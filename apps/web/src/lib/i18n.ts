export type Lang = "ar" | "en" | "tr";

export const LANGS: Lang[] = ["ar", "en", "tr"];

export function parseLang(raw: string | null | undefined): Lang {
  if (raw === "en" || raw === "tr" || raw === "ar") return raw;
  return "ar";
}

export function dirFor(lang: Lang): "rtl" | "ltr" {
  return lang === "ar" ? "rtl" : "ltr";
}

export function withLang(href: string, lang: Lang): string {
  if (lang === "ar") return href;
  const join = href.includes("?") ? "&" : "?";
  return `${href}${join}lang=${lang}`;
}

const STATUS: Record<Lang, Record<string, string>> = {
  ar: {
    SUPPORTED: "مؤيَّد بمصدر",
    CLOSE_WITH_DIFF: "قريب مع اختلاف",
    ATTRIBUTED_RULING: "حكم منسوب",
    UNDETERMINED: "لم يُحسم",
  },
  en: {
    SUPPORTED: "Supported by a source",
    CLOSE_WITH_DIFF: "Close, with differences",
    ATTRIBUTED_RULING: "Attributed ruling",
    UNDETERMINED: "Undetermined",
  },
  tr: {
    SUPPORTED: "Kaynakla destekleniyor",
    CLOSE_WITH_DIFF: "Yakın, farklılıklarla",
    ATTRIBUTED_RULING: "Atfedilen hüküm",
    UNDETERMINED: "Belirsiz",
  },
};

export type Messages = {
  navAria: string;
  navVerify: string;
  navHow: string;
  navAbout: string;
  navSources: string;
  navPrivacy: string;
  brand: string;
  brandSubtitle: string;
  homeLead: string;
  homeCtaVerify: string;
  homeCtaHow: string;
  homeBadge: string;
  clearText: string;
  samplesLabel: string;
  sample1: string;
  sample2: string;
  sample3: string;
  trustSources: string;
  trustPrivacy: string;
  trustNotFatwa: string;
  matchScoreLabel: string;
  fullMatch: string;
  matchPercent: string;
  inputQueryLabel: string;
  canonicalLabel: string;
  methodNoteTitle: string;
  auditId: string;
  resultTitle: string;
  engineVersion: string;
  backToVerify: string;
  diffAnalysisTitle: string;
  diffAnalysisLead: string;
  diffUserLabel: string;
  diffSourceLabel: string;
  diffLegendEqual: string;
  diffLegendInsert: string;
  diffLegendReplace: string;
  undeterminedLead: string;
  undeterminedStep1: string;
  undeterminedStep2: string;
  undeterminedStep3: string;
  undeterminedIntegrity: string;
  flagReview: string;
  shareCardLabel: string;
  shareCardSize: string;
  shareCardDisclosure: string;
  labelText: string;
  labelImage: string;
  buttonChooseImage: string;
  noFileSelected: string;
  placeholder: string;
  buttonVerify: string;
  buttonBusy: string;
  errRequired: string;
  ocrReview: string;
  ocrEmpty: string;
  ocrStub: string;
  newCheck: string;
  loading: string;
  cardMissing: string;
  idMissing: string;
  nearestMatch: string;
  sourceQuran: string;
  sourceHadith: string;
  knownClaim: string;
  rulingOf: string;
  diffs: string;
  supportedMeans: string;
  aiDisclosure: string;
  permanentLink: string;
  dataVersion: string;
  feedbackUsefulQ: string;
  feedbackUseful: string;
  feedbackWrong: string;
  feedbackComment: string;
  feedbackThanks: string;
  feedbackReported: string;
  shareCopy: string;
  shareCopied: string;
  shareNative: string;
  shareImage: string;
  shareImageDownload: string;
  shareImageBusy: string;
  shareImageSaved: string;
  shareWa: string;
  shareTg: string;
  shareX: string;
  viewSourceIsnad: string;
  aboutTitle: string;
  aboutLead: string;
  aboutP1: string;
  aboutP2: string;
  aboutP3: string;
  aboutP4: string;
  aboutP5: string;
  howTitle: string;
  howLead: string;
  howStatuses: string;
  howLimits: string;
  howEval: string;
  sourcesTitle: string;
  sourcesLeadApi: string;
  sourcesLicenses: string;
  landingTag: string;
  tamperDiff: string;
  correctAlt: string;
  fullSource: string;
  proofLink: string;
  meanings: string;
  copyCorrect: string;
  copyPoliteReply: string;
  copied: string;
  attributedRulings: string;
  rulingsFooter: string;
};

export const M: Record<Lang, Messages> = {
  ar: {
    navAria: "التنقل الرئيسي",
    navVerify: "تحقق",
    navHow: "كيف يعمل",
    navAbout: "عن الأداة",
    navSources: "المصادر",
    navPrivacy: "الخصوصية",
    brand: "مُحقِّق",
    brandSubtitle: "منظومة الإسناد النصي",
    homeLead: "الصق نصًا أو ارفع لقطة شاشة. الأداة مساعدة بالذكاء الاصطناعي وليست جهةٍ فتوى.",
    homeCtaVerify: "ابدأ التحقق",
    homeCtaHow: "كيف يعمل؟",
    homeBadge: "تدقيق فوري",
    clearText: "مسح النص",
    samplesLabel: "نماذج سريعة",
    sample1: "إنما الأعمال بالنيات",
    sample2: "المسلم من سلم المسلمون من لسانه ويده",
    sample3: "قل هو الله أحد",
    trustSources: "مطابقة مع مصادر مسندة مخزّنة",
    trustPrivacy: "لا نُخزّن نصّك الخام",
    trustNotFatwa: "ليست جهة فتوى شرعية",
    matchScoreLabel: "درجة التطابق النصي:",
    fullMatch: "تطابق تام (100%)",
    matchPercent: "تطابق {n}%",
    inputQueryLabel: "النص المدخل في الاستعلام:",
    canonicalLabel: "النص المحقق في المصدر:",
    methodNoteTitle: "تنبيه منهجي:",
    auditId: "معرف الفحص",
    resultTitle: "نتيجة التحقق والتوثيق",
    engineVersion: "إصدار البيانات",
    backToVerify: "العودة للتحقق",
    diffAnalysisTitle: "مقارنة الفروق اللفظية والضبط (Diff Analysis)",
    diffAnalysisLead:
      "يعرض هذا الفحص الفروق بين النص المدخل والأصل المخزّن في المصدر، كالتشكيل أو الإملاء أو اختصار المتن.",
    diffUserLabel: "النص المدخل (المستعلم عنه)",
    diffSourceLabel: "الأصل المحقق في المصدر",
    diffLegendEqual: "تطابق متطابق",
    diffLegendInsert: "ألفاظ متممة في المرجع",
    diffLegendReplace: "اختلاف تشكيل أو إملاء",
    undeterminedLead:
      "لم يُعثر على مطابقة كافية في المصادر المعتمدة. النظام يتوقف عن الحكم عند الشك.",
    undeterminedStep1: "راجع صياغة النص أو أزل الزوائد الإعلانية",
    undeterminedStep2: "جرّب مقطعًا أوضح من الآية أو المتن",
    undeterminedStep3: "عند الحاجة، ارجع لأهل الاختصاص",
    undeterminedIntegrity: "مبدأ التحرز: الامتناع عند الشك أفضل من حكم خاطئ.",
    flagReview: "الإبلاغ للمراجعة",
    shareCardLabel: "بطاقة مشاركة رقمية",
    shareCardSize: "١:١ للمشاركة",
    shareCardDisclosure: "تحقق من الرابط — أداة مساعدة وليست جهة فتوى",
    labelText: "النص للتحقق",
    labelImage: "أو صورة (اختياري، حتى 5MB)",
    buttonChooseImage: "اختر صورة",
    noFileSelected: "لم يُختر ملف",
    placeholder: "الصق النص المنسوب للقرآن أو الحديث هنا…",
    buttonVerify: "تحقق من النص",
    buttonBusy: "جارٍ التحقيق والمطابقة…",
    errRequired: "النص مطلوب",
    ocrReview: "راجع النص المستخرج ثم اضغط تحقق.",
    ocrEmpty:
      "لم يُستخرج نص من الصورة. جرّب صورة أوضح أو الصق الآية في المربع ثم اضغط تحقق.",
    ocrStub:
      "تعرّف الصورة غير مفعّل على الخادم (OCR=stub). الصق الآية في المربع ثم اضغط تحقق.",
    newCheck: "تحقق جديد",
    loading: "جارٍ التحميل…",
    cardMissing: "البطاقة غير موجودة",
    idMissing: "معرّف البطاقة مفقود",
    nearestMatch: "أقرب مطابقة",
    sourceQuran: "المصدر: القرآن",
    sourceHadith: "المصدر",
    knownClaim: "مطالبة معروفة",
    rulingOf: "حكم",
    diffs: "اختلافات (على النص بعد التطبيع)",
    supportedMeans:
      "«مؤيَّد بمصدر» يعني أن النص وُجد في المصدر المعتمد، لا أن الادعاء المحيط أو تطبيقه صحيح.",
    aiDisclosure: "أداة مساعدة بالذكاء الاصطناعي وليست جهة فتوى.",
    permanentLink: "رابط دائم",
    dataVersion: "إصدار البيانات",
    feedbackUsefulQ: "هل كانت النتيجة مفيدة؟",
    feedbackUseful: "مفيدة",
    feedbackWrong: "بلّغ عن خطأ",
    feedbackComment: "تعليق اختياري عند الإبلاغ",
    feedbackThanks: "شكرًا لملاحظاتك",
    feedbackReported: "تم استلام البلاغ — سنراجعه",
    shareCopy: "نسخ الرابط",
    shareCopied: "تم النسخ",
    shareNative: "مشاركة",
    shareImage: "مشاركة الصورة",
    shareImageDownload: "تنزيل الصورة",
    shareImageBusy: "جارٍ تجهيز الصورة…",
    shareImageSaved: "تم تنزيل الصورة",
    shareWa: "واتساب",
    shareTg: "تيليجرام",
    shareX: "X",
    viewSourceIsnad: "عرض المصدر والإسناد",
    aboutTitle: "عن مُحقِّق",
    aboutLead: "أداة مساعدة للتحقق من النصوص المنسوبة للقرآن والحديث الشائعة على وسائل التواصل.",
    aboutP1:
      "المراجع (الكتاب، الرقم، الحكم، اسم المحكِّم) تأتي فقط من بيانات مخزّنة. لا يولّد نموذج لغوي هذه الحقول.",
    aboutP2:
      "«مؤيَّد بمصدر» يعني أن النص وُجد في المصدر المعتمد، لا أن الادعاء المحيط أو تطبيقه صحيح.",
    aboutP3: "الأداة مساعدة بالذكاء الاصطناعي وليست جهة فتوى.",
    aboutP4:
      "الأسئلة الشخصية أو الخلافية تُحال إلى مصدر مؤهّل؛ الأداة لا تصدر فتاوى ولا أحكامًا على أشخاص أو جماعات.",
    aboutP5:
      "تخضع صياغة الحالات وقائمة المطالبات المعروفة لمراجعة علمية موثّقة في سجل المراجعة داخل المستودع قبل الاعتماد العام.",
    howTitle: "كيف يعمل مُحقِّق",
    howLead: "مطابقة حتمية مع مصادر مخزّنة — لا اختلاق للمراجع.",
    howStatuses: "حالات النتيجة",
    howLimits: "الحدود",
    howEval: "التقييم",
    sourcesTitle: "المصادر والتراخيص",
    sourcesLeadApi: "إصدار البيانات (API)",
    sourcesLicenses: "المصادر المستخدمة",
    landingTag: "تحقق سريع من النصوص الفيروسية المنسوبة للقرآن والحديث",
    tamperDiff: "كاشف التحريف بالفرق",
    correctAlt: "الصحيح البديل",
    fullSource: "النص الكامل في المصدر",
    proofLink: "رابط الإثبات",
    meanings: "معاني / ترجمات مخزّنة",
    copyCorrect: "نسخ النص الصحيح",
    copyPoliteReply: "نسخ ردّ مهذّب جاهز",
    copied: "تم النسخ",
    attributedRulings: "أحكام منسوبة",
    rulingsFooter: "قد يختلف الحكم بين المحدّثين؛ نعرض ما هو مخزّن فقط.",
  },
  en: {
    navAria: "Main navigation",
    navVerify: "Verify",
    navHow: "How it works",
    navAbout: "About",
    navSources: "Sources",
    navPrivacy: "Privacy",
    brand: "Muhaqqiq",
    brandSubtitle: "Text attribution system",
    homeLead: "Paste text or upload a screenshot. AI-assisted tool, not a fatwa authority.",
    homeCtaVerify: "Start verifying",
    homeCtaHow: "How it works",
    homeBadge: "Instant text check",
    clearText: "Clear text",
    samplesLabel: "Quick samples",
    sample1: "Actions are but by intention",
    sample2: "The Muslim is the one from whose tongue and hand Muslims are safe",
    sample3: "Say: He is Allah, the One",
    trustSources: "Matched against stored sourced corpora",
    trustPrivacy: "We do not store your raw text",
    trustNotFatwa: "Not a fatwa authority",
    matchScoreLabel: "Text match score:",
    fullMatch: "Exact match (100%)",
    matchPercent: "Match {n}%",
    inputQueryLabel: "Text you submitted:",
    canonicalLabel: "Verified source text:",
    methodNoteTitle: "Method note:",
    auditId: "Check id",
    resultTitle: "Verification result",
    engineVersion: "Data version",
    backToVerify: "Back to verify",
    diffAnalysisTitle: "Wording & vocalization diff (Diff Analysis)",
    diffAnalysisLead:
      "Shows differences between your input and the stored source text, such as spelling, diacritics, or a truncated quote.",
    diffUserLabel: "Your input",
    diffSourceLabel: "Stored source text",
    diffLegendEqual: "Matching text",
    diffLegendInsert: "Extra wording in the source",
    diffLegendReplace: "Spelling or diacritic difference",
    undeterminedLead:
      "No sufficient match was found in approved sources. The system abstains when unsure.",
    undeterminedStep1: "Revise wording or remove forward-spam extras",
    undeterminedStep2: "Try a clearer excerpt of the verse or hadith",
    undeterminedStep3: "When needed, consult a qualified specialist",
    undeterminedIntegrity: "Safety principle: abstaining when unsure is better than a false ruling.",
    flagReview: "Flag for review",
    shareCardLabel: "Digital share card",
    shareCardSize: "1:1 for sharing",
    shareCardDisclosure: "Verify via the link — AI-assisted tool, not a fatwa authority",
    labelText: "Text to verify",
    labelImage: "Or an image (optional, up to 5MB)",
    buttonChooseImage: "Choose image",
    noFileSelected: "No file selected",
    placeholder: "Paste text attributed to the Quran or hadith…",
    buttonVerify: "Verify text",
    buttonBusy: "Matching…",
    errRequired: "Text is required",
    ocrReview: "Review the extracted text, then verify.",
    ocrEmpty:
      "No text could be read from the image. Try a clearer crop, or paste the verse above then Verify.",
    ocrStub:
      "Image OCR is disabled on the server (OCR=stub). Paste the verse above, then Verify.",
    newCheck: "New check",
    loading: "Loading…",
    cardMissing: "Card not found",
    idMissing: "Missing card id",
    nearestMatch: "Nearest match",
    sourceQuran: "Source: Quran",
    sourceHadith: "Source",
    knownClaim: "Known claim",
    rulingOf: "Ruling of",
    diffs: "Differences (on normalized text)",
    supportedMeans:
      "“Supported” means the text was found in an approved source; it does not mean the surrounding claim or its application is correct.",
    aiDisclosure: "AI-assisted tool, not a fatwa authority.",
    permanentLink: "Permanent link",
    dataVersion: "Data version",
    feedbackUsefulQ: "Was this result useful?",
    feedbackUseful: "Useful",
    feedbackWrong: "Report a wrong result",
    feedbackComment: "Optional comment when reporting",
    feedbackThanks: "Thanks for your feedback",
    feedbackReported: "Report received — we will review it",
    shareCopy: "Copy link",
    shareCopied: "Copied",
    shareNative: "Share",
    shareImage: "Share image",
    shareImageDownload: "Download image",
    shareImageBusy: "Preparing image…",
    shareImageSaved: "Image downloaded",
    shareWa: "WhatsApp",
    shareTg: "Telegram",
    shareX: "X",
    viewSourceIsnad: "View source and chain",
    aboutTitle: "About Muhaqqiq",
    aboutLead: "A helper for checking viral texts attributed to the Quran or hadith.",
    aboutP1:
      "References (book, number, grade, grader) come only from stored data. A language model never generates them.",
    aboutP2:
      "“Supported” means the text exists in the approved source — not that the surrounding claim is correct.",
    aboutP3: "AI-assisted tool, not a fatwa authority.",
    aboutP4:
      "Personal or disputed questions are referred to a qualified source; the tool does not issue fatwas or rulings on people or groups.",
    aboutP5:
      "Status wording and the known-claims list follow a documented scholarly review process in the repository before public reliance.",
    howTitle: "How Muhaqqiq works",
    howLead: "Deterministic matching against stored sources — references are never invented.",
    howStatuses: "Result statuses",
    howLimits: "Limits",
    howEval: "Evaluation",
    sourcesTitle: "Sources and licenses",
    sourcesLeadApi: "Data version (API)",
    sourcesLicenses: "Sources in use",
    landingTag: "Fast checks for viral texts attributed to the Quran and hadith",
    tamperDiff: "Tamper detection (diff)",
    correctAlt: "Correct alternative",
    fullSource: "Full source text",
    proofLink: "Proof link",
    meanings: "Stored meanings / translations",
    copyCorrect: "Copy correct text",
    copyPoliteReply: "Copy polite reply",
    copied: "Copied",
    attributedRulings: "Attributed rulings",
    rulingsFooter: "Scholars may differ; we only show stored rulings.",
  },
  tr: {
    navAria: "Ana gezinme",
    navVerify: "Doğrula",
    navHow: "Nasıl çalışır",
    navAbout: "Hakkında",
    navSources: "Kaynaklar",
    navPrivacy: "Gizlilik",
    brand: "Muhaqqiq",
    brandSubtitle: "Metin isnat sistemi",
    homeLead:
      "Metin yapıştırın veya ekran görüntüsü yükleyin. Yapay zekâ destekli araçtır; fetva makamı değildir.",
    homeCtaVerify: "Doğrulamaya başla",
    homeCtaHow: "Nasıl çalışır?",
    homeBadge: "Anında metin kontrolü",
    clearText: "Metni temizle",
    samplesLabel: "Hızlı örnekler",
    sample1: "Ameller niyetlere göredir",
    sample2: "Müslüman, dilinden ve elinden diğer Müslümanların emin olduğu kimsedir",
    sample3: "De ki: O Allah birdir",
    trustSources: "Kayıtlı kaynaklarla eşleştirme",
    trustPrivacy: "Ham metninizi saklamayız",
    trustNotFatwa: "Fetva makamı değildir",
    matchScoreLabel: "Metin eşleşme skoru:",
    fullMatch: "Tam eşleşme (%100)",
    matchPercent: "Eşleşme %{n}",
    inputQueryLabel: "Gönderdiğiniz metin:",
    canonicalLabel: "Kaynaktaki doğrulanmış metin:",
    methodNoteTitle: "Yöntem notu:",
    auditId: "Kontrol kimliği",
    resultTitle: "Doğrulama sonucu",
    engineVersion: "Veri sürümü",
    backToVerify: "Doğrulamaya dön",
    diffAnalysisTitle: "Lafız ve hareke farkları (Diff Analysis)",
    diffAnalysisLead:
      "Girdiğiniz metin ile kayıtlı kaynak arasındaki farkları (yazım, hareke veya kısaltılmış alıntı) gösterir.",
    diffUserLabel: "Girdiğiniz metin",
    diffSourceLabel: "Kayıtlı kaynak metni",
    diffLegendEqual: "Eşleşen metin",
    diffLegendInsert: "Kaynakta tamamlayıcı lafız",
    diffLegendReplace: "Yazım veya hareke farkı",
    undeterminedLead:
      "Onaylı kaynaklarda yeterli eşleşme bulunamadı. Sistem emin değilse hüküm vermez.",
    undeterminedStep1: "İfadeyi gözden geçirin veya gereksiz ekleri kaldırın",
    undeterminedStep2: "Ayet veya hadisten daha net bir parça deneyin",
    undeterminedStep3: "Gerekirse ehil bir uzmana başvurun",
    undeterminedIntegrity: "İhtiyat ilkesi: şüphede durmak, hatalı hükümden iyidir.",
    flagReview: "İnceleme için bildir",
    shareCardLabel: "Dijital paylaşım kartı",
    shareCardSize: "Paylaşım için 1:1",
    shareCardDisclosure: "Bağlantıdan doğrulayın — yapay zekâ destekli araç, fetva makamı değildir",
    labelText: "Doğrulanacak metin",
    labelImage: "Veya görsel (isteğe bağlı, en fazla 5MB)",
    buttonChooseImage: "Görsel seç",
    noFileSelected: "Dosya seçilmedi",
    placeholder: "Kur'an veya hadise atfedilen metni yapıştırın…",
    buttonVerify: "Metni doğrula",
    buttonBusy: "Eşleştiriliyor…",
    errRequired: "Metin gerekli",
    ocrReview: "Çıkarılan metni gözden geçirin, sonra doğrulayın.",
    ocrEmpty:
      "Görselden metin okunamadı. Daha net bir kırpım deneyin veya ayeti yukarıya yapıştırıp Doğrula’ya basın.",
    ocrStub:
      "Sunucuda görsel OCR kapalı (OCR=stub). Ayetı yukarıya yapıştırıp Doğrula’ya basın.",
    newCheck: "Yeni kontrol",
    loading: "Yükleniyor…",
    cardMissing: "Kart bulunamadı",
    idMissing: "Kart kimliği eksik",
    nearestMatch: "En yakın eşleşme",
    sourceQuran: "Kaynak: Kur'an",
    sourceHadith: "Kaynak",
    knownClaim: "Bilinen iddia",
    rulingOf: "Hükmü",
    diffs: "Farklar (normalize metin üzerinde)",
    supportedMeans:
      "“Destekleniyor”, metnin onaylı kaynakta bulunduğu anlamına gelir; çevresindeki iddianın doğru olduğu anlamına gelmez.",
    aiDisclosure: "Yapay zekâ destekli bir araçtır; fetva makamı değildir.",
    permanentLink: "Kalıcı bağlantı",
    dataVersion: "Veri sürümü",
    feedbackUsefulQ: "Sonuç faydalı mıydı?",
    feedbackUseful: "Faydalı",
    feedbackWrong: "Hatalı sonuç bildir",
    feedbackComment: "Bildirim için isteğe bağlı yorum",
    feedbackThanks: "Geri bildiriminiz için teşekkürler",
    feedbackReported: "Bildirim alındı — inceleyeceğiz",
    shareCopy: "Bağlantıyı kopyala",
    shareCopied: "Kopyalandı",
    shareNative: "Paylaş",
    shareImage: "Görseli paylaş",
    shareImageDownload: "Görseli indir",
    shareImageBusy: "Görsel hazırlanıyor…",
    shareImageSaved: "Görsel indirildi",
    shareWa: "WhatsApp",
    shareTg: "Telegram",
    shareX: "X",
    viewSourceIsnad: "Kaynağı ve isnadı göster",
    aboutTitle: "Muhaqqiq hakkında",
    aboutLead: "Kur'an veya hadise atfedilen viral metinleri kontrol etmek için bir yardımcı araç.",
    aboutP1:
      "Referanslar (kitap, numara, derece, değerlendiren) yalnızca kayıtlı veriden gelir. Dil modeli bunları üretmez.",
    aboutP2:
      "“Destekleniyor”, metnin kaynakta var olduğu anlamına gelir — çevresindeki iddianın doğruluğu anlamına gelmez.",
    aboutP3: "Yapay zekâ destekli bir araçtır; fetva makamı değildir.",
    aboutP4:
      "Kişisel veya ihtilaflı sorular ehil bir kaynağa yönlendirilir; araç fetva vermez ve kişi/grup hakkında hüküm vermez.",
    aboutP5:
      "Durum ifadeleri ve bilinen iddialar listesi, kamuya güvenmeden önce depodaki belgelenmiş akademik inceleme sürecine tabidir.",
    howTitle: "Muhaqqiq nasıl çalışır",
    howLead: "Kayıtlı kaynaklara karşı deterministik eşleştirme — referans uydurulmaz.",
    howStatuses: "Sonuç durumları",
    howLimits: "Sınırlar",
    howEval: "Değerlendirme",
    sourcesTitle: "Kaynaklar ve lisanslar",
    sourcesLeadApi: "Veri sürümü (API)",
    sourcesLicenses: "Kullanılan kaynaklar",
    landingTag: "Kur'an ve hadise atfedilen viral metinler için hızlı kontrol",
    tamperDiff: "Tahrif fark dedektörü",
    correctAlt: "Doğru alternatif",
    fullSource: "Kaynaktaki tam metin",
    proofLink: "Kanıt bağlantısı",
    meanings: "Kayıtlı anlamlar / çeviriler",
    copyCorrect: "Doğru metni kopyala",
    copyPoliteReply: "Kibarca yanıtı kopyala",
    copied: "Kopyalandı",
    attributedRulings: "Atfedilen hükümler",
    rulingsFooter: "Muhaddisler farklı hükmedebilir; yalnızca kayıtlı olanları gösteririz.",
  },
};

export function t(lang: Lang): Messages {
  return M[lang];
}

export function statusLabel(lang: Lang, status: string, fallback?: string): string {
  return STATUS[lang][status] || fallback || status;
}
