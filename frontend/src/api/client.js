const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function ingestRepo(repoUrl) {
  const response = await fetch(`${API_BASE_URL}/ingest`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ repo_url: repoUrl }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Ingest request failed: ${response.status} ${errorText}`);
  }

  return response.json();
}

export async function getIngestStatus(jobId) {
  const response = await fetch(`${API_BASE_URL}/ingest/${jobId}`);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Status request failed: ${response.status} ${errorText}`);
  }

  return response.json();
}

export async function queryRepo(repoId, query) {
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ repo_id: repoId, query }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Query request failed: ${response.status} ${errorText}`);
  }

  return response.json();
}
