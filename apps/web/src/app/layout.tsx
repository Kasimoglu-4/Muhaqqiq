import type { Metadata, Viewport } from "next";
import { Amiri, IBM_Plex_Sans_Arabic } from "next/font/google";
import { Nav } from "@/components/Nav";
import "./globals.css";

const uiFont = IBM_Plex_Sans_Arabic({
  subsets: ["arabic", "latin"],
  weight: ["400", "600", "700"],
  variable: "--font-ui",
  display: "swap",
});

const verseFont = Amiri({
  subsets: ["arabic", "latin"],
  weight: ["400", "700"],
  variable: "--font-verse",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "مُحقِّق",
    template: "%s · مُحقِّق",
  },
  description: "تحقق سريع من النصوص المنسوبة للقرآن والحديث",
  applicationName: "مُحقِّق",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    title: "مُحقِّق",
  },
};

export const viewport: Viewport = {
  themeColor: "#f1fcf5",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="ar"
      dir="rtl"
      suppressHydrationWarning
      className={`${uiFont.variable} ${verseFont.variable}`}
    >
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){var m=location.search.match(/[?&]lang=(en|tr)\\b/);if(m){document.documentElement.lang=m[1];document.documentElement.dir="ltr";}})();`,
          }}
        />
      </head>
      <body className={uiFont.className}>
        <Nav />
        <div className="shell">{children}</div>
        <script
          dangerouslySetInnerHTML={{
            __html: `if('serviceWorker' in navigator){window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));}`,
          }}
        />
      </body>
    </html>
  );
}
