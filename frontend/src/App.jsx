import { useState } from "react";
import ChatPanel from "./components/ChatPanel.jsx";
import IngestPanel from "./components/IngestPanel.jsx";

function App() {
  const [activeRepoId, setActiveRepoId] = useState(null);

  return (
    <div style={{ minHeight: "100vh", background: "#f1f5f9", color: "#111827" }}>
      <header style={{ padding: "1.5rem 2rem", background: "#ffffff", borderBottom: "1px solid #e5e7eb" }}>
        <h1 style={{ margin: 0, fontSize: "1.75rem" }}>Repo AI Engineer</h1>
        <p style={{ margin: "0.5rem 0 0", color: "#4b5563" }}>
          Chat with the repository in the center, then inspect source snippets on the right.
        </p>
      </header>

      <main
        style={{
          display: "grid",
          gridTemplateColumns: "320px minmax(0, 1fr)",
          gap: "1rem",
          padding: "1.5rem 2rem",
        }}
      >
        <aside style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: "1rem", padding: "1.25rem" }}>
          <IngestPanel onRepoReady={setActiveRepoId} />
        </aside>

        <section style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <ChatPanel repoId={activeRepoId} />
        </section>
      </main>
    </div>
  );
}

export default App;
