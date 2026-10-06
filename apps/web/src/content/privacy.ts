export type PrivacyLang = "ar" | "en" | "tr";

/**
 * Public privacy copy — short, user-facing; must not contradict implemented behavior.
 */
export const PRIVACY: Record<
  PrivacyLang,
  { title: string; paragraphs: string[] }
> = {
  ar: {
    title: "الخصوصية",
    paragraphs: [
      "لا نحفظ النص الذي تلصقه. نحتفظ فقط بملخص مشفّر للحالة، ومراجع المصدر، والدرجة، وإصدار البيانات على بطاقة عامة يمكن فتحها بالرابط.",
      "صور التحقق تُعالَج لاستخراج النص ثم تُحذف؛ لا نخزّن الصورة.",
      "زر «مفيدة» أو «بلّغ عن خطأ» يسجّل ملاحظة مجهولة (نوع البلاغ ومعرّف البطاقة، وتعليق اختياري عند الإبلاغ).",
      "سجلات التشغيل بلا نصك. لا تتبع إعلاني في التطبيق.",
      "الأداة مساعدة بالذكاء الاصطناعي وليست جهة فتوى.",
    ],
  },
  en: {
    title: "Privacy",
    paragraphs: [
      "We do not keep the text you paste. Cards store a hashed summary, status, source references, score, and data version on a public link.",
      "Verification images are processed to extract text, then discarded — we do not keep the image.",
      "Useful / Report a wrong result saves an anonymous note (kind, card id, optional comment when reporting).",
      "Operational logs never include your text. No ad tracking in the app.",
      "AI-assisted tool, not a fatwa authority.",
    ],
  },
  tr: {
    title: "Gizlilik",
    paragraphs: [
      "Yapıştırdığınız metni saklamayız. Kartlarda özet (hash), durum, kaynak referansları, skor ve veri sürümü tutulur; bağlantıyla herkese açık olabilir.",
      "Doğrulama görselleri metin çıkarmak için işlenir, sonra silinir — görüntüyü saklamayız.",
      "Faydalı / Hatalı sonuç bildir anonim bir not kaydeder (tür, kart kimliği, bildirimde isteğe bağlı yorum).",
      "İşletim kayıtlarında metniniz yoktur. Uygulamada reklam takibi yoktur.",
      "Yapay zekâ destekli bir araçtır; fetva makamı değildir.",
    ],
  },
};
