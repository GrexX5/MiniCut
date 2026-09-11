"use client";

import { useEffect, useRef, useState } from "react";
import ClipSlider from "@/components/ClipSlider";
import {
  createJob,
  downloadUrl,
  fetchInfo,
  fetchJob,
  fetchQuota,
  type VideoMeta,
} from "@/lib/api";
import { detectSource, SOURCE_LABEL } from "@/lib/source";
import { formatSecondsToHms, parseHmsToSeconds } from "@/lib/time";

type Phase = "idle" | "fetching" | "ready" | "processing" | "done" | "error";

const SUGGESTED_CLIP = 20; // PRD §4 : extrait 10–30s par défaut

export default function Home() {
  const [url, setUrl] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [meta, setMeta] = useState<VideoMeta | null>(null);
  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(SUGGESTED_CLIP);
  const [startTxt, setStartTxt] = useState("00:00");
  const [endTxt, setEndTxt] = useState("00:20");
  const [progress, setProgress] = useState(0);
  const [download, setDownload] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [quota, setQuota] = useState({ used: 0, limit: 10 });
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  const source = detectSource(url);

  useEffect(() => {
    fetchQuota().then(setQuota);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  function syncTimes(s: number, e: number) {
    setStart(s);
    setEnd(e);
    setStartTxt(formatSecondsToHms(s));
    setEndTxt(formatSecondsToHms(e));
  }

  async function handleAnalyze() {
    setError("");
    setDownload(null);
    if (!url.trim()) {
      setError("Colle d'abord un lien YouTube, Instagram ou TikTok.");
      return;
    }
    if (source === "unknown") {
      setError("Lien non reconnu : seuls YouTube, Instagram et TikTok sont supportés en MVP.");
      return;
    }
    setPhase("fetching");
    try {
      const m = await fetchInfo(url.trim());
      setMeta(m);
      const d = Math.floor(m.duration || 0);
      // Extrait par défaut : 0 → min(20s, durée)
      const e = d > 0 ? Math.min(SUGGESTED_CLIP, d) : SUGGESTED_CLIP;
      syncTimes(0, e);
      setPhase("ready");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Échec de lecture de la vidéo.");
      setPhase("error");
    }
  }

  function applyManual(which: "start" | "end", raw: string) {
    if (which === "start") setStartTxt(raw);
    else setEndTxt(raw);
    try {
      const s = which === "start" ? parseHmsToSeconds(raw) : start;
      const e = which === "end" ? parseHmsToSeconds(raw) : end;
      const d = meta?.duration || 0;
      if (s < 0 || e <= s) return;
      if (d && (s >= d || e > d)) return;
      if (e - s > 300) {
        setError("Extrait trop long : 5 min max en MVP.");
        return;
      }
      setStart(s);
      setEnd(e);
      setError("");
    } catch {
      /* saisie en cours : on ne bloque pas */
    }
  }

  async function handleClip(full = false) {
    setError("");
    setDownload(null);
    if (!meta) return;
    const d = Math.floor(meta.duration || 0);
    const s = full ? 0 : Math.round(start);
    const e = full ? d || Math.round(end) : Math.round(end);
    if (!(e > s)) {
      setError("La fin doit être après le début.");
      return;
    }
    setPhase("processing");
    setProgress(0);
    try {
      const { job_id, quota: q } = await createJob(url.trim(), s, e);
      setQuota(q);
      // Polling toutes les 2s (Rapport §1 : workers async, pas de timeout)
      pollRef.current = setInterval(async () => {
        try {
          const st = await fetchJob(job_id);
          setProgress(st.progress);
          if (st.status === "done") {
            if (pollRef.current) clearInterval(pollRef.current);
            setDownload(downloadUrl(st.download_url));
            setPhase("done");
          } else if (st.status === "error") {
            if (pollRef.current) clearInterval(pollRef.current);
            setError(st.error || "Échec du traitement.");
            setPhase("error");
          }
        } catch (err) {
          if (pollRef.current) clearInterval(pollRef.current);
          setError(err instanceof Error ? err.message : "Suivi du job impossible.");
          setPhase("error");
        }
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Création du job impossible.");
      setPhase("ready");
    }
  }

  const busy = phase === "fetching" || phase === "processing";
  const clipLen = Math.max(0, Math.round(end - start));

  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-50 to-white text-zinc-900 dark:from-black dark:to-zinc-950 dark:text-zinc-100">
      {/* Header */}
      <header className="mx-auto flex w-full max-w-5xl items-center justify-between px-4 py-5 sm:px-6">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-fuchsia-600 text-lg font-black text-white">
            ✂
          </div>
          <span className="text-xl font-extrabold tracking-tight">Mini Cut</span>
        </div>
        <div className="rounded-full border border-zinc-200 px-3 py-1 text-xs font-medium text-zinc-600 dark:border-zinc-800 dark:text-zinc-400">
          Quota : {quota.used}/{quota.limit} aujourd&apos;hui
        </div>
      </header>

      <main className="mx-auto w-full max-w-3xl px-4 pb-20 sm:px-6">
        {/* Hero — PRD §4 étape 1 */}
        <section className="pt-6 text-center sm:pt-10">
          <h1 className="text-3xl font-extrabold leading-tight tracking-tight sm:text-5xl">
            Extraits YouTube, Insta & TikTok{" "}
            <span className="bg-gradient-to-r from-violet-600 to-fuchsia-600 bg-clip-text text-transparent">
              sans filigrane
            </span>
          </h1>
          <p className="mx-auto mt-3 max-w-xl text-sm text-zinc-600 dark:text-zinc-400 sm:text-base">
            Colle ton lien, choisis 10–30 secondes au curseur, télécharge en MP4. En moins de 3
            clics, sans télécharger la vidéo entière.
          </p>
        </section>

        {/* Input universel — PRD §3.1 */}
        <section className="mt-6 rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 sm:p-5">
          <label htmlFor="url" className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Lien vidéo
          </label>
          <div className="mt-2 flex flex-col gap-2 sm:flex-row">
            <input
              id="url"
              type="url"
              inputMode="url"
              placeholder="https://www.youtube.com/watch?v=… / tiktok.com/… / instagram.com/reel/…"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
              className="h-12 flex-1 rounded-xl border border-zinc-300 bg-zinc-50 px-4 text-sm outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-200 dark:border-zinc-700 dark:bg-zinc-950"
            />
            <button
              onClick={handleAnalyze}
              disabled={busy}
              className="h-12 rounded-xl bg-zinc-900 px-6 text-sm font-bold text-white transition hover:bg-zinc-700 disabled:opacity-50 dark:bg-white dark:text-black dark:hover:bg-zinc-200"
            >
              {phase === "fetching" ? "Analyse…" : "Analyser"}
            </button>
          </div>
          {url.trim() && (
            <p className="mt-2 text-xs font-medium text-zinc-500">
              Source détectée :{" "}
              <span className="rounded-full bg-violet-100 px-2 py-0.5 text-violet-700 dark:bg-violet-950 dark:text-violet-300">
                {SOURCE_LABEL[source]}
              </span>
            </p>
          )}
          {phase === "fetching" && (
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
              <div className="h-full w-1/2 animate-pulse rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500" />
            </div>
          )}
        </section>

        {error && (
          <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
            {error}
          </div>
        )}

        {/* Métadonnées + clipping — PRD §3.2 */}
        {meta && (phase === "ready" || phase === "processing" || phase === "done") && (
          <section className="mt-4 rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 sm:p-5">
            <div className="flex flex-col gap-4 sm:flex-row">
              {meta.thumbnail && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={meta.thumbnail}
                  alt={meta.title}
                  className="h-40 w-full rounded-xl object-cover sm:w-56"
                />
              )}
              <div className="min-w-0 flex-1">
                <p className="text-[11px] font-bold uppercase tracking-wide text-fuchsia-600">
                  {meta.source} · {meta.duration_hms}
                </p>
                <h2 className="mt-1 line-clamp-2 font-bold leading-snug">{meta.title}</h2>
                {meta.uploader && <p className="mt-1 text-xs text-zinc-500">par {meta.uploader}</p>}
              </div>
            </div>

            <div className="mt-5">
              <ClipSlider
                duration={meta.duration || Math.max(end, 60)}
                start={start}
                end={end}
                onChange={(s, e) => {
                  setStart(s);
                  setEnd(e);
                  setStartTxt(formatSecondsToHms(s));
                  setEndTxt(formatSecondsToHms(e));
                }}
              />
              {/* Saisie manuelle précise */}
              <div className="mt-3 grid grid-cols-2 gap-2">
                <label className="text-xs font-medium text-zinc-500">
                  Début (HH:MM:SS)
                  <input
                    value={startTxt}
                    onChange={(e) => applyManual("start", e.target.value)}
                    className="mt-1 h-10 w-full rounded-lg border border-zinc-300 bg-zinc-50 px-3 font-mono text-sm outline-none focus:border-violet-500 dark:border-zinc-700 dark:bg-zinc-950"
                  />
                </label>
                <label className="text-xs font-medium text-zinc-500">
                  Fin (HH:MM:SS)
                  <input
                    value={endTxt}
                    onChange={(e) => applyManual("end", e.target.value)}
                    className="mt-1 h-10 w-full rounded-lg border border-zinc-300 bg-zinc-50 px-3 font-mono text-sm outline-none focus:border-fuchsia-500 dark:border-zinc-700 dark:bg-zinc-950"
                  />
                </label>
              </div>
            </div>

            {/* Actions — PRD §4 étape 4 */}
            <div className="mt-4 flex flex-col gap-2 sm:flex-row">
              <button
                onClick={() => handleClip(false)}
                disabled={busy}
                className="h-12 flex-1 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 px-6 text-sm font-bold text-white shadow transition hover:opacity-90 disabled:opacity-50"
              >
                {phase === "processing"
                  ? `Découpe… ${Math.round(progress * 100)}%`
                  : `Couper & Télécharger (${clipLen}s)`}
              </button>
              <button
                onClick={() => handleClip(true)}
                disabled={busy || !(meta.duration > 0)}
                title="Télécharger la vidéo complète"
                className="h-12 rounded-xl border border-zinc-300 px-6 text-sm font-bold transition hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
              >
                Vidéo complète
              </button>
            </div>

            {/* Processing — PRD §3.3 */}
            {phase === "processing" && (
              <div className="mt-4">
                <div className="h-2.5 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 transition-all"
                    style={{ width: `${Math.round(progress * 100)}%` }}
                  />
                </div>
                <p className="mt-2 text-center text-xs text-zinc-500">
                  Le serveur télécharge uniquement ton extrait puis le découpe… ne ferme pas
                  l&apos;onglet.
                </p>
              </div>
            )}

            {/* Delivery — PRD §4 étape 6 */}
            {phase === "done" && download && (
              <div className="mt-4 rounded-xl bg-green-50 p-4 text-center dark:bg-green-950">
                <p className="text-sm font-bold text-green-700 dark:text-green-300">
                  Ton extrait est prêt 🎉
                </p>
                <a
                  href={download}
                  download
                  className="mt-3 inline-flex h-12 items-center rounded-xl bg-green-600 px-8 text-sm font-bold text-white transition hover:bg-green-500"
                >
                  ⬇ Télécharger le MP4
                </a>
                <p className="mt-2 text-[11px] text-green-700/70 dark:text-green-300/70">
                  Lien valable 10 min sur le serveur (nettoyage auto), puis à conserver.
                </p>
              </div>
            )}
          </section>
        )}

        {/* SEO / explication */}
        <section className="mt-10 grid gap-3 text-center sm:grid-cols-3 sm:text-left">
          {[
            ["1. Colle", "YouTube, TikTok ou Instagram. Détection auto."],
            ["2. Coupe", "Double curseur + saisie HH:MM:SS précise."],
            ["3. Télécharge", "MP4 sans filigrane, en quelques secondes."],
          ].map(([t, d]) => (
            <div
              key={t}
              className="rounded-2xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
            >
              <p className="font-extrabold">{t}</p>
              <p className="mt-1 text-xs text-zinc-500">{d}</p>
            </div>
          ))}
        </section>
      </main>

      <footer className="border-t border-zinc-200 py-6 text-center text-xs text-zinc-500 dark:border-zinc-800">
        Mini Cut MVP — YouTube · Instagram · TikTok — Fichiers supprimés après 10 min.
      </footer>
    </div>
  );
}
