"use client";
import React, { useState, useRef } from "react";
import { startGeneration } from "./claude_adapter";

const C = {
  bg: "#09111f",
  surface: "#0f1e33",
  card: "#111f38",
  border: "#1c3054",
  accent: "#38bdf8",
  green: "#34d399",
  purple: "#a78bfa",
  red: "#f87171",
  yellow: "#fbbf24",
  text: "#cbd5e1",
  muted: "#475569",
  heading: "#f1f5f9",
};

const SOURCES = [
  { id: "q_open", label: "Questionnaires – Open Text", group: "Questionnaire" },
  { id: "lab_blood", label: "Lab – Blood Chemistry/Haematology", group: "Laboratory" },
  { id: "diary_ae", label: "Diaries – Adverse Events", group: "Diary" },
  { id: "vitals", label: "Vital Signs Measurements", group: "Clinical" },
];

const Lbl = ({ children, mt }: any) => (
  <div style={{ color: C.muted, fontSize: 10, letterSpacing: 1, marginBottom: 4, marginTop: mt || 0 }}>{children}</div>
);

const Inp = ({ value, onChange, ...p }: any) => (
  <input
    value={value}
    onChange={(e) => onChange(e.target.value)}
    style={{
      width: "100%",
      background: C.surface,
      border: `1px solid ${C.border}`,
      borderRadius: 6,
      color: C.heading,
      padding: "8px 10px",
      fontSize: 12,
      fontFamily: "monospace",
      outline: "none",
      boxSizing: "border-box",
    }}
    {...p}
  />
);

const Txta = ({ value, onChange, placeholder }: any) => (
  <textarea
    value={value}
    onChange={(e) => onChange(e.target.value)}
    placeholder={placeholder}
    rows={3}
    style={{
      width: "100%",
      background: C.surface,
      border: `1px solid ${C.border}`,
      borderRadius: 6,
      color: C.heading,
      padding: "8px 10px",
      fontSize: 12,
      fontFamily: "monospace",
      resize: "vertical",
      outline: "none",
      boxSizing: "border-box",
    }}
  />
);

const SumRow = ({ label, value }: any) => (
  <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: `1px solid ${C.border}`, fontSize: 11 }}>
    <span style={{ color: C.muted }}>{label}</span>
    <span style={{ color: C.text, fontFamily: "monospace" }}>{value}</span>
  </div>
);

function PipelineDiagram({ cfg }: any) {
  const groups = [...new Set(SOURCES.filter((s) => cfg.dataSources.includes(s.id)).map((s) => s.group))];
  return (
    <div style={{ background: C.bg, padding: 12, borderRadius: 8 }}>
      <div style={{ color: C.accent, fontSize: 13, fontFamily: "monospace", fontWeight: "bold", marginBottom: 8 }}>{cfg.projectName} — Clinical Data Pipeline</div>
      <div style={{ color: C.muted, fontSize: 11, marginBottom: 8 }}>Sources: {groups.join(', ')}</div>
    </div>
  );
}

export default function App() {
  const [cfg, setCfg] = useState({
    projectName: "STUDY001",
    description: "",
    language: "R",
    nSubjects: 50,
    dataSources: ["q_open", "lab_blood", "diary_ae"],
    messTypes: ["missing", "typos"],
    messinessLevel: 2,
    sdtmDomains: ["DM", "AE", "LB"],
    adamDomains: ["ADSL"],
    additionalNotes: "",
  });

  const [phase, setPhase] = useState("idle");
  const [status, setStatus] = useState<any>(null);
  const [jobInfo, setJobInfo] = useState<any>(null);
  const abortRef = useRef<AbortController | null>(null);

  const set = (k: string, v: any) => setCfg((c: any) => ({ ...c, [k]: v }));

  const generate = async () => {
    setPhase("running");
    try {
      const { jobId, downloadUrl } = await startGeneration(cfg, (st: any) => {
        setStatus(st);
      });
      setJobInfo({ jobId, downloadUrl });
      setPhase("done");
    } catch (e: any) {
      setPhase("error");
      setStatus({ error: String(e) });
    }
  };

  return (
    <div style={{ background: C.bg, minHeight: "100vh", color: C.text, fontFamily: "system-ui,sans-serif", padding: 16 }}>
      <div style={{ textAlign: "center", marginBottom: 22 }}>
        <div style={{ color: C.accent, fontSize: 17, fontFamily: "monospace", fontWeight: "bold", letterSpacing: 2 }}>⚗ CDISC DUMMY DATA GENERATOR</div>
        <div style={{ color: C.muted, fontSize: 11, marginTop: 4 }}>Clinical Research Pipeline Scaffolding Tool (Ollama)</div>
      </div>

      <div style={{ maxWidth: 900, margin: "0 auto" }}>
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 22 }}>
          <div style={{ color: C.heading, fontWeight: "bold", fontSize: 13, marginBottom: 14, fontFamily: "monospace" }}>Project Setup</div>

          <Lbl>Project / Study Name</Lbl>
          <Inp value={cfg.projectName} onChange={(v: any) => set('projectName', v.toUpperCase().replace(/\s/g, '_'))} placeholder="STUDY001" />
          <Lbl mt={14}>Brief Description (optional)</Lbl>
          <Txta value={cfg.description} onChange={(v: any) => set('description', v)} placeholder="Study title, therapeutic area, phase, sponsor…" />

          <div style={{ marginTop: 16 }}>
            <Lbl>Data Sources</Lbl>
            <div style={{ display: 'flex', gap: 8 }}>
              {SOURCES.map(s => (
                <button key={s.id} onClick={() => {
                  const ds = cfg.dataSources.includes(s.id) ? cfg.dataSources.filter((x: any) => x !== s.id) : [...cfg.dataSources, s.id];
                  set('dataSources', ds);
                }} style={{ background: cfg.dataSources.includes(s.id) ? C.accent : 'transparent', border: `1px solid ${C.border}`, color: cfg.dataSources.includes(s.id) ? C.bg : C.muted, padding: '6px 10px', borderRadius: 6 }}>{s.label}</button>
              ))}
            </div>
          </div>

          <div style={{ marginTop: 18 }}>
            <Lbl>SDTM Domains</Lbl>
            <Inp value={cfg.sdtmDomains.join(', ')} onChange={(v: any) => set('sdtmDomains', v.split(',').map((x: string) => x.trim()).filter(Boolean))} />
          </div>

          <div style={{ marginTop: 18 }}>
            <SumRow label="Project" value={cfg.projectName} />
            <SumRow label="Language" value={cfg.language} />
            <SumRow label="N Subjects" value={cfg.nSubjects} />
            <SumRow label="Data Sources" value={`${cfg.dataSources.length} selected`} />
            <SumRow label="SDTM Domains" value={cfg.sdtmDomains.join(', ') || '—'} />
          </div>

          <div style={{ marginTop: 18 }}>
            {phase !== 'running' && <button onClick={generate} style={{ width: '100%', padding: 14, borderRadius: 8, border: 'none', cursor: 'pointer', background: 'linear-gradient(135deg,#0ea5e9,#6366f1)', color: 'white', fontSize: 14, fontFamily: 'monospace', fontWeight: 'bold' }}>▶  GENERATE PROJECT</button>}
            {phase === 'running' && <div style={{ padding: 14, borderRadius: 8, background: C.surface }}>Generating…</div>}
            {phase === 'error' && <div style={{ marginTop: 12, color: C.red }}>{status?.error}</div>}
          </div>
        </div>

        <div style={{ marginTop: 18 }}>
          <PipelineDiagram cfg={cfg} />
        </div>

        {phase === 'done' && jobInfo && (
          <div style={{ marginTop: 18, background: C.card, padding: 14, borderRadius: 8 }}>
            <div style={{ color: C.heading, fontWeight: 'bold', marginBottom: 8 }}>Result</div>
            <div style={{ color: C.muted }}>Job ID: <span style={{ color: C.text }}>{jobInfo.jobId}</span></div>
            <div style={{ marginTop: 8 }}>
              <a href={jobInfo.downloadUrl} style={{ background: 'linear-gradient(135deg,#064e3b,#0f2d5c)', color: C.green, padding: '8px 12px', borderRadius: 6, display: 'inline-block', textDecoration: 'none' }}>↓ Download ZIP</a>
            </div>
          </div>
        )}

        {status && (
          <div style={{ marginTop: 12, background: C.surface, padding: 10, borderRadius: 6 }}>
            <div style={{ color: C.muted, fontSize: 11 }}>Status</div>
            <pre style={{ color: C.text, fontSize: 12, whiteSpace: 'pre-wrap' }}>{JSON.stringify(status, null, 2)}</pre>
          </div>
        )}

      </div>
    </div>
  );
}
