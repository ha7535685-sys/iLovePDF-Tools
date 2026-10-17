const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/tools";
const POLL_INTERVAL_MS = 1500;
const MAX_POLL_ATTEMPTS = 3000; // 10 minutes max

export interface JobResult {
  filename: string;
  downloadUrl: string;
  elapsedTime?: number;
}

/**
 * POST files to an endpoint, poll for completion, return download info.
 * @param endpoint  e.g. "/merge"
 * @param body      FormData with all fields
 * @param onStatus  optional callback for status messages
 */
export async function submitAndPoll(
  endpoint: string,
  body: FormData,
  onStatus?: (msg: string) => void
): Promise<JobResult> {
  // 1. Submit the job
  onStatus?.("Uploading file…");
  const postRes = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    body,
  });

  if (!postRes.ok) {
    let detail = "Upload failed";
    try {
      const err = await postRes.json();
      detail = err.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }

  const postData = await postRes.json();
  const job_id = postData.job_id;
  if (!job_id) throw new Error("Server did not return a job ID.");

  // If already completed in the POST response (instant serverless execution)
  if (postData.status === "completed") {
    const timeInfo = postData.elapsed_time !== undefined && postData.elapsed_time !== null ? ` in ${postData.elapsed_time}s` : "";
    onStatus?.(`Completed${timeInfo}! Downloading…`);
    return {
      filename: postData.filename,
      downloadUrl: postData.download_url || `${API_BASE}/download/${job_id}`,
      elapsedTime: postData.elapsed_time,
    };
  }
  if (postData.status === "failed") {
    throw new Error(postData.error ?? "Conversion failed on the server.");
  }

  // 2. Poll until done (fallback for background processing)
  onStatus?.("Processing…");
  const pollInterval = 200; // Fast fixed interval
  
  for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt++) {
    const pollRes = await fetch(`${API_BASE}/jobs/${job_id}`);
    if (!pollRes.ok) throw new Error("Polling request failed");

    const data = await pollRes.json();

    if (data.status === "completed") {
      const timeInfo = data.elapsed_time !== undefined && data.elapsed_time !== null ? ` in ${data.elapsed_time}s` : "";
      onStatus?.(`Completed${timeInfo}! Downloading…`);
      return {
        filename: data.filename,
        downloadUrl: `${API_BASE}/download/${job_id}`,
        elapsedTime: data.elapsed_time,
      };
    }
    if (data.status === "failed") {
      throw new Error(data.error ?? "Conversion failed on the server.");
    }
    
    // still processing — wait a short bit before polling again
    await new Promise((r) => setTimeout(r, pollInterval));
  }

  throw new Error("Conversion timed out. Please try again.");
}

/** Trigger a file download in the browser from a URL. */
export function triggerDownload(url: string, filename: string) {
  const a = document.createElement("a");
  a.style.display = "none";
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
