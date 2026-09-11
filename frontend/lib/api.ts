/** Client API — parle au backend FastAPI (Rapport §1 : polling, pas de timeout). */
const BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export interface VideoMeta {
  source: string;
  title: string;
  thumbnail: string;
  duration: number;
  duration_hms: string;
  uploader: string;
  webpage_url: string;
}

async function handle(res: Response) {
  if (!res.ok) {
    let detail = `Erreur ${res.status}`;
    try {
      const j = await res.json();
      detail = j.detail || j.error || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function fetchInfo(url: string): Promise<VideoMeta> {
  const res = await fetch(`${BASE}/api/info`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  const json = await handle(res);
  if (!json.ok) throw new Error(json.error || "Vidéo illisible");
  return json.data as VideoMeta;
}

export async function createJob(url: string, start: number, end: number) {
  const res = await fetch(`${BASE}/api/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, start, end }),
  });
  const json = await handle(res);
  return json as { job_id: string; quota: { used: number; limit: number } };
}

export interface JobStatus {
  job_id: string;
  status: "queued" | "processing" | "done" | "error";
  progress: number;
  download_url: string | null;
  error: string;
}

export async function fetchJob(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${BASE}/api/jobs/${jobId}`, { cache: "no-store" });
  const json = await handle(res);
  return json as JobStatus;
}

export function downloadUrl(path: string | null): string | null {
  if (!path) return null;
  return `${BASE}${path}`;
}

export async function fetchQuota(): Promise<{ used: number; limit: number }> {
  try {
    const res = await fetch(`${BASE}/api/quota`, { cache: "no-store" });
    const json = await res.json();
    return { used: json.used ?? 0, limit: json.limit ?? 10 };
  } catch {
    return { used: 0, limit: 10 };
  }
}

export { BASE as API_BASE };
