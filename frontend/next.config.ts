import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // Miniatures YouTube / Instagram / TikTok (PRD §3.2)
    remotePatterns: [
      { protocol: "https", hostname: "**.ytimg.com" },
      { protocol: "https", hostname: "**.youtube.com" },
      { protocol: "https", hostname: "**.tiktokcdn.com" },
      { protocol: "https", hostname: "**.tiktokcdn-us.com" },
      { protocol: "https", hostname: "**.cdninstagram.com" },
      { protocol: "https", hostname: "**.fbcdn.net" },
    ],
  },
};

export default nextConfig;
