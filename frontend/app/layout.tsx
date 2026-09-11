import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Mini Cut — Extraits YouTube, TikTok, Instagram sans filigrane",
  description:
    "Colle un lien YouTube, TikTok ou Instagram, choisis 10-30 secondes au curseur et télécharge ton extrait MP4 sans filigrane en moins de 3 clics.",
  keywords: ["youtube cut", "tiktok download sans filigrane", "instagram reel download", "extraire extrait vidéo"],
  openGraph: {
    title: "Mini Cut — l'outil le plus rapide pour extraire des portions de vidéos",
    description: "Découpage précis YouTube / TikTok / Instagram sans filigrane.",
    type: "website",
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="fr"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
