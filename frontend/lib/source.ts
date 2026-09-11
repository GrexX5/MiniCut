/** PRD §3.1 — détection instantanée côté front (badge YouTube/Instagram/TikTok). */
export type Source = "youtube" | "instagram" | "tiktok" | "unknown";

export function detectSource(url: string): Source {
  const u = (url || "").trim();
  if (/youtube\.com\/(watch|shorts|live|embed)|youtu\.be\//i.test(u)) return "youtube";
  if (/instagram\.com\/(reel|reels|p|tv)\//i.test(u)) return "instagram";
  if (/tiktok\.com\/|vm\.tiktok\.com|vt\.tiktok\.com/i.test(u)) return "tiktok";
  return "unknown";
}

export const SOURCE_LABEL: Record<Source, string> = {
  youtube: "YouTube",
  instagram: "Instagram",
  tiktok: "TikTok",
  unknown: "Lien",
};
