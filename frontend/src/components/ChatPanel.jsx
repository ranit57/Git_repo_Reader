import { useEffect, useRef, useState } from "react";
import AnswerCard from "./AnswerCard.jsx";
import { queryRepo } from "../api/client.js";

const initialMessages = [
  { role: "assistant", text: "Hello! Ask anything about your repository in this chat." },
];

const sampleQuestions = [
  "What does this repository do?",
  "Where is the main entry point or app logic?",
  "Find potential bugs or exceptions in the code.",
  "Which files define the main data model or schema?",
  "Explain how dependencies are loaded in this repo.",
];

function ChatPanel({ repoId }) {
  const [messages, setMessages] = useState(initialMessages);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const trimmed = draft.trim();
    if (!trimmed || isSending) return;

    if (!repoId) {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          text: "Ingest a repository before asking a question.",
        },
      ]);
      return;
    }

    setMessages((current) => [...current, { role: "user", text: trimmed }]);
    setDraft("");
    setIsSending(true);

    try {
      const data = await queryRepo(repoId, trimmed);
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          text: data.answer ?? "No answer returned from the backend.",
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          text: `Query failed: ${error.message}`,
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  const statusStyles = isSending
    ? { background: "#fff7ed", color: "#9a3412", borderColor: "#fed7aa" }
    : repoId
      ? { background: "#ecfdf5", color: "#047857", borderColor: "#bbf7d0" }
      : { background: "#f1f5f9", color: "#64748b", borderColor: "#e2e8f0" };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "calc(100vh - 150px)",
        background: "#f8fafc",
        border: "1px solid #dbe3ef",
        borderRadius: "1rem",
        padding: "1rem",
        boxShadow: "0 16px 40px rgba(15, 23, 42, 0.06)",
      }}
    >
      <div style={{ marginBottom: "1rem", display: "flex", justifyContent: "space-between", gap: "1rem", alignItems: "center" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: "1.15rem", color: "#0f172a" }}>Repository Chat</h2>
          <p style={{ margin: "0.35rem 0 0", color: "#64748b" }}>
            {repoId ? `Active repo: ${repoId}` : "Ingest a repository to unlock answers."}
          </p>
        </div>
        <span
          style={{
            padding: "0.38rem 0.65rem",
            borderRadius: "999px",
            border: `1px solid ${statusStyles.borderColor}`,
            fontSize: "0.78rem",
            fontWeight: 700,
            whiteSpace: "nowrap",
            ...statusStyles,
          }}
        >
          {isSending ? "Generating" : repoId ? "Ready" : "Waiting"}
        </span>
      </div>

      <div style={{ marginBottom: "1rem", padding: "0.85rem", background: "#ffffff", borderRadius: "0.75rem", border: "1px solid #e2e8f0" }}>
        <div style={{ marginBottom: "0.65rem", fontWeight: 700, color: "#0f172a", fontSize: "0.9rem" }}>Try one of these questions</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
          {sampleQuestions.map((question) => (
            <button
              key={question}
              type="button"
              onClick={() => setDraft(question)}
              style={{
                border: "1px solid #dbe3ef",
                background: "#f8fafc",
                color: "#334155",
                borderRadius: "999px",
                padding: "0.45rem 0.7rem",
                cursor: "pointer",
                fontSize: "0.82rem",
                fontWeight: 600,
              }}
            >
              {question}
            </button>
          ))}
        </div>
      </div>

      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "0.35rem 0.35rem 0.35rem 0",
          display: "grid",
          gap: "0.9rem",
          alignContent: "start",
        }}
      >
        {messages.map((message, index) => (
          <AnswerCard key={index} role={message.role} text={message.text} />
        ))}
        <div ref={endRef} />
      </div>

      {isSending ? (
        <div style={{ marginTop: "0.75rem", color: "#64748b", fontSize: "0.88rem" }}>
          Reading retrieved context and shaping the answer...
        </div>
      ) : null}

      <div style={{ marginTop: "1rem", display: "flex", gap: "0.75rem", alignItems: "flex-end" }}>
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about the repository..."
          rows={3}
          style={{
            flex: 1,
            padding: "0.9rem 1rem",
            borderRadius: "0.75rem",
            border: "1px solid #cbd5e1",
            resize: "vertical",
            fontSize: "0.95rem",
            lineHeight: 1.5,
            outline: "none",
            background: "#ffffff",
            color: "#0f172a",
          }}
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={isSending || !repoId}
          style={{
            padding: "0.9rem 1.2rem",
            borderRadius: "0.75rem",
            border: "none",
            background: isSending || !repoId ? "#94a3b8" : "#2563eb",
            color: "white",
            cursor: isSending || !repoId ? "not-allowed" : "pointer",
            fontWeight: 700,
            minWidth: "120px",
            boxShadow: isSending || !repoId ? "none" : "0 10px 22px rgba(37, 99, 235, 0.22)",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatPanel;
