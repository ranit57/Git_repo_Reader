import { useEffect, useState } from "react";
import { ingestRepo, getIngestStatus } from "../api/client.js";

function normalizeRepoUrl(url) {
  try {
    const parsed = new URL(url);
    return `${parsed.protocol}//${parsed.hostname}${parsed.pathname.replace(/\/+$/, "")}`;
  } catch {
    return url;
  }
}

function IngestPanel({ onRepoReady }) {
  const [repoUrl, setRepoUrl] = useState("");
  const [status, setStatus] = useState("Enter a GitHub repo URL to ingest.");
  const [isLoading, setIsLoading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [jobState, setJobState] = useState(null);
  const [jobMessage, setJobMessage] = useState(null);
  const [jobCurrentStep, setJobCurrentStep] = useState(null);
  const [jobActiveAgent, setJobActiveAgent] = useState(null);
  const [jobLog, setJobLog] = useState([]);

  useEffect(() => {
    if (!jobId) {
      return;
    }

    let interval = null;
    const pollStatus = async () => {
      try {
        const data = await getIngestStatus(jobId);
        setJobState(data.state);
        setJobMessage(data.message ?? data.error ?? "No details provided.");
        setJobCurrentStep(data.current_step ?? null);
        setJobActiveAgent(data.active_agent ?? null);
        setJobLog((current) => [
          ...current,
          `${new Date().toLocaleTimeString()}: ${data.current_step ?? "unknown"} (${data.active_agent ?? "unknown"}) - ${data.message ?? data.error ?? "No details provided."}`,
        ]);

        if (data.state === "ready" || data.state === "failed") {
          clearInterval(interval);
          setIsLoading(false);
          if (data.state === "ready" && data.repo_id) {
            onRepoReady?.(data.repo_id);
          }
          setStatus(
            data.state === "ready"
              ? `Ingestion complete: ${data.state}`
              : `Ingestion failed: ${data.message ?? data.error}`
          );
        }
      } catch (error) {
        clearInterval(interval);
        setIsLoading(false);
        setStatus(`Status polling failed: ${error.message}`);
      }
    };

    pollStatus();
    interval = window.setInterval(pollStatus, 3000);

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [jobId, onRepoReady]);

  const handleIngest = async () => {
    const trimmed = repoUrl.trim();
    if (!trimmed) {
      setStatus("Please enter a repository URL first.");
      return;
    }

    const normalizedUrl = normalizeRepoUrl(trimmed);

    try {
      setIsLoading(true);
      setStatus("Submitting ingestion request...");
      setJobId(null);
      setJobState(null);
      setJobMessage(null);
      setJobCurrentStep(null);
      setJobActiveAgent(null);

      const data = await ingestRepo(normalizedUrl);
      setJobId(data.job_id ?? null);
      if (data.repo_id) {
        onRepoReady?.(data.repo_id);
      }
      setStatus(`Ingestion queued. Job ID: ${data.job_id}`);
    } catch (error) {
      setStatus(`Failed to ingest repo: ${error.message}`);
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>Ingest Repository</h2>
      <p style={{ color: "#6b7280", lineHeight: 1.7 }}>
        Enter a GitHub repo URL and press the button to ingest it into the backend.
      </p>

      <label style={{ display: "block", marginBottom: "0.75rem", fontWeight: 600, color: "#374151" }}>
        Repository URL
      </label>
      <input
        value={repoUrl}
        onChange={(event) => setRepoUrl(event.target.value)}
        placeholder="https://github.com/owner/repo.git"
        style={{
          width: "100%",
          padding: "0.9rem 1rem",
          borderRadius: "0.85rem",
          border: "1px solid #d1d5db",
          fontSize: "0.95rem",
          marginBottom: "1rem",
        }}
      />

      <button
        type="button"
        onClick={handleIngest}
        disabled={isLoading}
        style={{
          width: "100%",
          padding: "0.95rem 1rem",
          borderRadius: "0.85rem",
          border: "none",
          background: "#2563eb",
          color: "white",
          cursor: isLoading ? "not-allowed" : "pointer",
          fontWeight: 700,
        }}
      >
        {isLoading ? "Ingesting..." : "Start ingestion"}
      </button>

      <div style={{ marginTop: "1rem", color: "#4b5563", fontSize: "0.95rem", lineHeight: 1.6 }}>
        {status}
      </div>

      {jobId ? (
        <div style={{ marginTop: "0.75rem", color: "#111827", fontWeight: 600 }}>
          <div>Job ID: {jobId}</div>
          <div>State: {jobState ?? "pending"}</div>
          {jobCurrentStep ? <div>Current Step: {jobCurrentStep}</div> : null}
          {jobActiveAgent ? <div>Active Agent: {jobActiveAgent}</div> : null}
          <div style={{ marginTop: "0.25rem", fontWeight: 400, color: "#4b5563" }}>
            {jobMessage}
          </div>
          {jobLog.length ? (
            <div style={{ marginTop: "1rem", padding: "0.75rem", background: "#f8fafc", borderRadius: "0.75rem", border: "1px solid #e2e8f0" }}>
              <div style={{ fontWeight: 700, marginBottom: "0.5rem" }}>Progress log</div>
              <div style={{ maxHeight: "180px", overflowY: "auto", fontSize: "0.85rem", color: "#475569" }}>
                {jobLog.map((entry, index) => (
                  <div key={index} style={{ marginBottom: "0.4rem" }}>
                    {entry}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export default IngestPanel;
