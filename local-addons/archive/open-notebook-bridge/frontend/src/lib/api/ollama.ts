export async function generateExport(payload: any) {
  const res = await fetch('/api/ollama/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getStatus(jobId: string) {
  const res = await fetch(`/api/ollama/status/${jobId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function downloadUrl(jobId: string) {
  return `/api/ollama/exports/${jobId}/download`;
}
