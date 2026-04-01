"use client";
import React, { useState, useEffect } from "react";
import { generateExport, getStatus, downloadUrl } from "../lib/api/ollama";

export default function OllamaBridge({ initialConfig }: any) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const start = async () => {
    setLoading(true);
    try {
      const resp = await generateExport(initialConfig || {});
      setJobId(resp.job_id);
    } catch (e) {
      alert(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!jobId) return;
    let mounted = true;
    const iv = setInterval(async () => {
      try {
        const s = await getStatus(jobId);
        if (!mounted) return;
        setStatus(s);
        if (s && s.status === "completed") {
          clearInterval(iv);
        }
      } catch (e) {
        console.error(e);
      }
    }, 2000);
    return () => {
      mounted = false;
      clearInterval(iv);
    };
  }, [jobId]);

  return (
    <div>
      <button onClick={start} disabled={loading || !!jobId}>
        {loading ? "Starting…" : jobId ? "Running…" : "Generate (Ollama)"}
      </button>
      {jobId && (
        <div>
            <div>Status: {status?.status || "pending"}</div>
            <a href={downloadUrl(jobId)}>Download ZIP</a>
          </div>
      )}
    </div>
  );
}
