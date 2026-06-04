import React from "react";

export default function CorpusTracker() {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    const token = localStorage.getItem("admin_token");
    fetch("/api/admin/corpus", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then(setData)
      .catch(() => setError("Failed to load corpus data"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={styles.hint}>Loading...</p>;
  if (error) return <p style={styles.error}>{error}</p>;
  if (!data || !data.texts || data.texts.length === 0)
    return <p style={styles.hint}>No texts ingested yet.</p>;

  return (
    <div>
      <p style={styles.summary}>
        {data.total_texts} texts · {data.total_chunks?.toLocaleString()} chunks
      </p>
      <div style={styles.tableWrapper}>
        <table style={styles.table}>
          <thead>
            <tr>
              {["Text", "Devanagari", "Category", "Authenticity", "Chunks", "Status", "Updated"].map((h) => (
                <th key={h} style={styles.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.texts.map((t) => (
              <tr key={t.text_name} style={styles.tr}>
                <td style={styles.td}>{t.text_name}</td>
                <td style={{ ...styles.td, fontFamily: "'Noto Serif Devanagari', serif" }}>
                  {t.title_devanagari}
                </td>
                <td style={styles.td}>{t.category}</td>
                <td style={styles.td}>
                  <span style={t.authenticity === "confirmed" ? styles.confirmed : styles.attributed}>
                    {t.authenticity}
                  </span>
                </td>
                <td style={{ ...styles.td, textAlign: "right" }}>{t.chunk_count}</td>
                <td style={styles.td}>
                  <span style={t.status === "ingested" ? styles.ingested : styles.pending}>
                    {t.status}
                  </span>
                </td>
                <td style={styles.td}>{t.last_updated?.slice(0, 10)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const styles = {
  summary: { color: "#b89b6a", fontSize: "0.9rem", marginBottom: "1rem" },
  tableWrapper: { overflowX: "auto" },
  table: { width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" },
  th: {
    color: "#6b5c3e",
    textAlign: "left",
    padding: "0.5rem 0.75rem",
    borderBottom: "1px solid rgba(232,213,163,0.15)",
    whiteSpace: "nowrap",
  },
  tr: { borderBottom: "1px solid rgba(232,213,163,0.06)" },
  td: { color: "#e8d5a3", padding: "0.5rem 0.75rem", verticalAlign: "middle" },
  confirmed: { color: "#7ab87a", fontSize: "0.8rem" },
  attributed: { color: "#b89b6a", fontSize: "0.8rem" },
  ingested: { color: "#7ab87a", fontSize: "0.8rem" },
  pending: { color: "#e0a060", fontSize: "0.8rem" },
  hint: { color: "#6b5c3e", fontSize: "0.9rem" },
  error: { color: "#e07070", fontSize: "0.9rem" },
};
