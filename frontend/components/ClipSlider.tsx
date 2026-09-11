"use client";

import { formatSecondsToHms } from "@/lib/time";

interface Props {
  duration: number;
  start: number;
  end: number;
  onChange: (start: number, end: number) => void;
}

/** PRD §3.2 — Timeline interactive à double curseur (début/fin). */
export default function ClipSlider({ duration, start, end, onChange }: Props) {
  const max = Math.max(1, Math.floor(duration));
  const clampStart = Math.min(Math.max(0, start), end - 1);
  const clampEnd = Math.min(Math.max(clampStart + 1, end), max);
  const leftPct = (clampStart / max) * 100;
  const rightPct = (clampEnd / max) * 100;

  return (
    <div className="w-full">
      <div className="relative h-10 select-none">
        {/* piste */}
        <div className="absolute top-1/2 h-2 w-full -translate-y-1/2 rounded-full bg-zinc-200 dark:bg-zinc-800" />
        {/* sélection */}
        <div
          className="absolute top-1/2 h-2 -translate-y-1/2 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500"
          style={{ left: `${leftPct}%`, width: `${Math.max(0, rightPct - leftPct)}%` }}
        />
        {/* curseur début */}
        <input
          type="range"
          aria-label="Début de l'extrait"
          min={0}
          max={max}
          step={1}
          value={Math.round(clampStart)}
          onChange={(e) => {
            const v = Number(e.target.value);
            onChange(Math.min(v, Math.round(clampEnd) - 1), Math.round(clampEnd));
          }}
          className="pointer-events-none absolute inset-0 h-10 w-full cursor-pointer appearance-none bg-transparent [&::-webkit-slider-thumb]:pointer-events-auto [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-white [&::-webkit-slider-thumb]:bg-violet-600 [&::-webkit-slider-thumb]:shadow [&::-moz-range-thumb]:pointer-events-auto [&::-moz-range-thumb]:h-5 [&::-moz-range-thumb]:w-5 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-white [&::-moz-range-thumb]:bg-violet-600"
        />
        {/* curseur fin */}
        <input
          type="range"
          aria-label="Fin de l'extrait"
          min={0}
          max={max}
          step={1}
          value={Math.round(clampEnd)}
          onChange={(e) => {
            const v = Number(e.target.value);
            onChange(Math.round(clampStart), Math.max(v, Math.round(clampStart) + 1));
          }}
          className="pointer-events-none absolute inset-0 h-10 w-full cursor-pointer appearance-none bg-transparent [&::-webkit-slider-thumb]:pointer-events-auto [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-white [&::-webkit-slider-thumb]:bg-fuchsia-600 [&::-webkit-slider-thumb]:shadow [&::-moz-range-thumb]:pointer-events-auto [&::-moz-range-thumb]:h-5 [&::-moz-range-thumb]:w-5 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-white [&::-moz-range-thumb]:bg-fuchsia-600"
        />
      </div>
      <div className="mt-1 flex items-center justify-between text-sm font-medium tabular-nums">
        <span className="rounded-md bg-violet-100 px-2 py-0.5 text-violet-700 dark:bg-violet-950 dark:text-violet-300">
          ▶ {formatSecondsToHms(clampStart)}
        </span>
        <span className="text-zinc-500">
          Extrait : {(clampEnd - clampStart).toFixed(0)}s / {formatSecondsToHms(max)}
        </span>
        <span className="rounded-md bg-fuchsia-100 px-2 py-0.5 text-fuchsia-700 dark:bg-fuchsia-950 dark:text-fuchsia-300">
          {formatSecondsToHms(clampEnd)} ◀
        </span>
      </div>
    </div>
  );
}
