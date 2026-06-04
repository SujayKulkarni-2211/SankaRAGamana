import React from "react";

export default function ResponseCard({ message }) {
  const [showSources, setShowSources] = React.useState(false);
  const sources = message.sources || [];

  return (
    <div style={styles.card}>
      <p style={styles.question}>{message.question}</p>
      <div style={styles.divider} />
      <p style={styles.answer}>{message.answer}</p>

      {sources.length > 0 && (
        <div style={styles.sourcesSection}>
          <button style={styles.toggle} onClick={() => setShowSources((s) => !s)}>
            {showSources ? "▲ Hide sources" : `▼ Sources (${sources.length})`}
          </button>
          {showSources && (
            <div style={styles.sources}>
              {sources.map((s, i) => (
                <div key={i} style={styles.source}>
                  <p style={styles.sourceMeta}>
                    {s.text_name} {s.verse_number ? `· v.${s.verse_number}` : ""}
                    {s.authenticity === "confirmed" && (
                      <span style={styles.confirmed}> confirmed</span>
                    )}
                  </p>
                  <p style={styles.sourceContent}>{s.content}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const styles = {
  card: {
    background: "rgba(232,213,163,0.04)",
    border: "1px solid rgba(232,213,163,0.1)",
    borderRadius: 10,
    padding: "1.25rem 1.5rem",
  },
  question: {
    color: "#6b5c3e",
    fontSize: "0.9rem",
    fontStyle: "italic",
    marginBottom: "0.75rem",
  },
  divider: {
    height: 1,
    background: "rgba(232,213,163,0.1)",
    marginBottom: "0.75rem",
  },
  answer: {
    color: "#e8d5a3",
    fontSize: "1rem",
    lineHeight: 1.75,
    fontFamily: "'Noto Sans Devanagari', sans-serif",
    whiteSpace: "pre-wrap",
  },
  sourcesSection: { marginTop: "1rem" },
  toggle: {
    background: "transparent",
    border: "none",
    color: "#6b5c3e",
    fontSize: "0.8rem",
    cursor: "pointer",
    padding: 0,
  },
  sources: { marginTop: "0.5rem", display: "flex", flexDirection: "column", gap: "0.75rem" },
  source: {
    background: "rgba(232,213,163,0.03)",
    border: "1px solid rgba(232,213,163,0.08)",
    borderRadius: 6,
    padding: "0.75rem",
  },
  sourceMeta: { color: "#b89b6a", fontSize: "0.8rem", marginBottom: "0.4rem" },
  sourceContent: {
    color: "rgba(232,213,163,0.7)",
    fontSize: "0.9rem",
    fontFamily: "'Noto Serif Devanagari', serif",
    lineHeight: 1.6,
  },
  confirmed: { color: "#7ab87a", fontStyle: "normal" },
};
