import { toPng } from "html-to-image";

/** True when the device is likely a phone/tablet that can share files. */
export function canNativeFileShare(): boolean {
  if (typeof navigator === "undefined") return false;
  const coarse =
    typeof window !== "undefined" && window.matchMedia("(pointer: coarse)").matches;
  if (!coarse && !/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) {
    return false;
  }
  return typeof navigator.canShare === "function";
}

export async function exportNodeToPng(node: HTMLElement): Promise<string> {
  // skipFonts avoids CSSStyleSheet.cssRules on cross-origin sheets (SecurityError).
  return toPng(node, {
    pixelRatio: 2,
    cacheBust: true,
    backgroundColor: "#ffffff",
    skipFonts: true,
    fontEmbedCSS: "",
  });
}

export function downloadDataUrl(dataUrl: string, filename: string) {
  const a = document.createElement("a");
  a.href = dataUrl;
  a.download = filename;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
}
