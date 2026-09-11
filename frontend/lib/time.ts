/** Utils temporels — miroir de backend/app/utils/timeparse.py (PRD §3.2). */

export function parseHmsToSeconds(value: string | number): number {
  if (typeof value === "number") {
    if (!Number.isFinite(value) || value < 0) throw new Error("Temps invalide");
    return value;
  }
  const s = (value || "").trim();
  if (!s) throw new Error("Temps vide");
  const asNum = Number(s);
  if (Number.isFinite(asNum) && s.match(/^\d+(\.\d+)?$/)) {
    if (asNum < 0) throw new Error("Temps invalide");
    return asNum;
  }
  const parts = s.split(":").map((p) => Number(p));
  if (parts.some((n) => !Number.isFinite(n) || n < 0)) {
    throw new Error(`Format invalide : '${value}' (attendu HH:MM:SS)`);
  }
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  throw new Error(`Format invalide : '${value}' (attendu HH:MM:SS)`);
}

export function formatSecondsToHms(total: number): string {
  const sec = Math.max(0, Math.round(total));
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  const mm = String(m).padStart(2, "0");
  const ss = String(s).padStart(2, "0");
  return h > 0 ? `${String(h).padStart(2, "0")}:${mm}:${ss}` : `${mm}:${ss}`;
}
