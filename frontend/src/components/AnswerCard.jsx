function InlineText({ text, isUser }) {
  const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g).filter(Boolean);

  return parts.map((part, index) => {
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code
          key={index}
          style={{
            padding: "0.08rem 0.35rem",
            borderRadius: "0.35rem",
            background: isUser ? "rgba(255,255,255,0.16)" : "#eef2f7",
            color: isUser ? "white" : "#0f172a",
            fontFamily: "Consolas, Monaco, monospace",
            fontSize: "0.88em",
          }}
        >
          {part.slice(1, -1)}
        </code>
      );
    }

    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }

    return <span key={index}>{part}</span>;
  });
}

function MarkdownResponse({ text, isUser }) {
  const lines = text.split("\n");
  const elements = [];
  let listItems = [];
  let codeLines = [];
  let inCode = false;

  const flushList = () => {
    if (!listItems.length) return;

    elements.push(
      <ul
        key={`list-${elements.length}`}
        style={{
          margin: "0.45rem 0 0.85rem",
          paddingLeft: "1.25rem",
          lineHeight: 1.65,
        }}
      >
        {listItems.map((item, index) => (
          <li key={index} style={{ marginBottom: "0.25rem" }}>
            <InlineText text={item} isUser={isUser} />
          </li>
        ))}
      </ul>
    );
    listItems = [];
  };

  const flushCode = () => {
    if (!codeLines.length) return;

    elements.push(
      <pre
        key={`code-${elements.length}`}
        style={{
          margin: "0.75rem 0",
          padding: "0.9rem 1rem",
          overflowX: "auto",
          borderRadius: "0.6rem",
          background: "#0f172a",
          color: "#e5e7eb",
          fontSize: "0.86rem",
          lineHeight: 1.55,
          border: "1px solid #1e293b",
        }}
      >
        <code>{codeLines.join("\n")}</code>
      </pre>
    );
    codeLines = [];
  };

  lines.forEach((line) => {
    const trimmed = line.trim();

    if (trimmed.startsWith("```")) {
      if (inCode) {
        flushCode();
      } else {
        flushList();
      }
      inCode = !inCode;
      return;
    }

    if (inCode) {
      codeLines.push(line);
      return;
    }

    if (!trimmed) {
      flushList();
      return;
    }

    if (trimmed.startsWith("### ")) {
      flushList();
      elements.push(
        <h4 key={`h4-${elements.length}`} style={{ margin: "0.9rem 0 0.35rem", fontSize: "0.98rem", color: "#111827" }}>
          {trimmed.slice(4)}
        </h4>
      );
      return;
    }

    if (trimmed.startsWith("## ")) {
      flushList();
      elements.push(
        <h3 key={`h3-${elements.length}`} style={{ margin: "1rem 0 0.4rem", fontSize: "1.08rem", color: "#0f172a" }}>
          {trimmed.slice(3)}
        </h3>
      );
      return;
    }

    if (trimmed.startsWith("# ")) {
      flushList();
      elements.push(
        <h2 key={`h2-${elements.length}`} style={{ margin: "0.25rem 0 0.5rem", fontSize: "1.16rem", color: "#0f172a" }}>
          {trimmed.slice(2)}
        </h2>
      );
      return;
    }

    if (trimmed === "---") {
      flushList();
      elements.push(
        <div key={`rule-${elements.length}`} style={{ height: 1, background: "#e2e8f0", margin: "0.85rem 0" }} />
      );
      return;
    }

    if (/^[-*]\s+/.test(trimmed)) {
      listItems.push(trimmed.replace(/^[-*]\s+/, ""));
      return;
    }

    flushList();
    elements.push(
      <p key={`p-${elements.length}`} style={{ margin: "0.45rem 0", lineHeight: 1.7 }}>
        <InlineText text={line} isUser={isUser} />
      </p>
    );
  });

  flushList();
  if (inCode || codeLines.length) {
    flushCode();
  }

  return <>{elements}</>;
}

function AnswerCard({ role, text }) {
  const isUser = role === "user";

  return (
    <article
      style={{
        justifySelf: isUser ? "end" : "start",
        width: isUser ? "fit-content" : "min(100%, 760px)",
        maxWidth: isUser ? "78%" : "100%",
        borderRadius: isUser ? "0.9rem 0.9rem 0.25rem 0.9rem" : "0.9rem 0.9rem 0.9rem 0.25rem",
        padding: isUser ? "0.8rem 1rem" : "1.05rem 1.15rem",
        background: isUser ? "#2563eb" : "#ffffff",
        color: isUser ? "white" : "#1f2937",
        border: isUser ? "1px solid #2563eb" : "1px solid #dbe3ef",
        boxShadow: isUser ? "0 8px 18px rgba(37, 99, 235, 0.16)" : "0 10px 28px rgba(15, 23, 42, 0.08)",
        wordBreak: "break-word",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.55rem",
          marginBottom: isUser ? "0.35rem" : "0.75rem",
          color: isUser ? "rgba(255,255,255,0.86)" : "#64748b",
          fontSize: "0.78rem",
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: "0.04em",
        }}
      >
        <span
          style={{
            width: "0.5rem",
            height: "0.5rem",
            borderRadius: "999px",
            background: isUser ? "rgba(255,255,255,0.76)" : "#10b981",
          }}
        />
        {isUser ? "You" : "Repo Answer"}
      </div>

      <div style={{ fontSize: "0.96rem", lineHeight: 1.65 }}>
        {isUser ? <InlineText text={text} isUser={isUser} /> : <MarkdownResponse text={text} isUser={isUser} />}
      </div>
    </article>
  );
}

export default AnswerCard;
