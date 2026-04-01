import { generateExport, getStatus, downloadUrl } from "../lib/api/ollama";

type ProgressCb = (status: any) => void;

export async function startGeneration(
  cfg: any,
  onProgress?: ProgressCb,
  pollInterval = 2000
) {
  // Submit job
  const resp = await generateExport(cfg);
  const jobId = resp.job_id;

  // Poll status until completed or failed
  let finished = false;
  while (!finished) {
    const st = await getStatus(jobId);
    onProgress?.(st);
    if (st.status === "completed" || st.status === "failed" || st.status === "error") {
      finished = true;
      break;
    }
    await new Promise((r) => setTimeout(r, pollInterval));
  }

  return { jobId, downloadUrl: downloadUrl(jobId) };
}
