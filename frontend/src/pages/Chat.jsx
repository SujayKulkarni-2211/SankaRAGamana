import React from "react";
import QueryBox from "../components/QueryBox";
import ResponseCard from "../components/ResponseCard";

export default function Chat() {
  const [messages, setMessages] = React.useState([]);
  const [loading, setLoading] = React.useState(false);

  async function handleQuery(question) {
    setLoading(true);
    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      setMessages((prev) => [{ question, ...data }, ...prev]);
    } catch (e) {
      setMessages((prev) => [
        { question, answer: "Connection error. Please try again.", sources: [] },
        ...prev,
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>SankaRĀGamana</h1>
        <p style={styles.subtitle}>अथातो ब्रह्म जिज्ञासा</p>
        <p style={styles.desc}>Ask Śaṅkarācārya — in Sanskrit, English, or Kannada</p>
      </header>

      <main style={styles.main}>
        {messages.length === 0 && !loading && (
          <div style={styles.empty}>
            <p style={styles.emptyText}>तत्त्वमसि</p>
            <p style={styles.emptyHint}>Begin your inquiry below</p>
          </div>
        )}
        {loading && (
          <div style={styles.loadingCard}>
            <span style={styles.loadingDot} />
            <span style={styles.loadingDot} />
            <span style={styles.loadingDot} />
          </div>
        )}
        {messages.map((msg, i) => (
          <ResponseCard key={i} message={msg} />
        ))}
      </main>

      <footer style={styles.footer}>
        <QueryBox onSubmit={handleQuery} disabled={loading} />
      </footer>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    minHeight: "100vh",
    maxWidth: 800,
    margin: "0 auto",
    padding: "0 1rem",
  },
  header: {
    textAlign: "center",
    padding: "2rem 0 1rem",
    borderBottom: "1px solid rgba(232,213,163,0.15)",
  },
  title: {
    fontSize: "2rem",
    fontFamily: "'Noto Serif Devanagari', serif",
    color: "#e8d5a3",
    letterSpacing: "0.05em",
  },
  subtitle: {
    fontSize: "1.1rem",
    color: "#b89b6a",
    marginTop: "0.4rem",
    fontFamily: "'Noto Serif Devanagari', serif",
  },
  desc: {
    fontSize: "0.85rem",
    color: "#6b5c3e",
    marginTop: "0.5rem",
  },
  main: {
    flex: 1,
    display: "flex",
    flexDirection: "column-reverse",
    gap: "1.5rem",
    padding: "1.5rem 0",
    overflowY: "auto",
  },
  empty: {
    textAlign: "center",
    padding: "4rem 0",
  },
  emptyText: {
    fontSize: "3rem",
    color: "rgba(232,213,163,0.2)",
    fontFamily: "'Noto Serif Devanagari', serif",
  },
  emptyHint: {
    fontSize: "0.85rem",
    color: "rgba(232,213,163,0.3)",
    marginTop: "0.5rem",
  },
  loadingCard: {
    display: "flex",
    gap: "0.5rem",
    padding: "1rem",
    justifyContent: "center",
  },
  loadingDot: {
    width: 8,
    height: 8,
    borderRadius: "50%",
    background: "#b89b6a",
    display: "inline-block",
    animation: "pulse 1.4s infinite ease-in-out",
  },
  footer: {
    position: "sticky",
    bottom: 0,
    background: "#0e0c09",
    paddingBottom: "1.5rem",
    paddingTop: "0.75rem",
    borderTop: "1px solid rgba(232,213,163,0.1)",
  },
};
