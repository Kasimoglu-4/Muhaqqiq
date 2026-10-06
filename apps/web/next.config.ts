import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Cloudflare Pages: static export (no next-on-pages / Workers adapter).
  output: "export",
  images: { unoptimized: true },
};

export default nextConfig;
