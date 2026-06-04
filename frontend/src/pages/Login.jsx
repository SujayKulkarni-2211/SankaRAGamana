import React from "react";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [username, setUsername] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const navigate = useNavigate();

  async function handleLogin(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        setError("Invalid credentials");
        return;
      }
      const data = await res.json();
      localStorage.setItem("admin_token", data.access_token);
      navigate("/admin");
    } catch {
      setError("Connection error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>Admin</h2>
        <p style={styles.subtitle}>SankaRĀGamana</p>
        <form onSubmit={handleLogin} style={styles.form}>
          <input
            style={styles.input}
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            style={styles.input}
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p style={styles.error}>{error}</p>}
          <button style={styles.button} type="submit" disabled={loading}>
            {loading ? "..." : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  card: {
    background: "rgba(232,213,163,0.05)",
    border: "1px solid rgba(232,213,163,0.15)",
    borderRadius: 8,
    padding: "2.5rem",
    width: "100%",
    maxWidth: 360,
  },
  title: { color: "#e8d5a3", fontSize: "1.5rem", textAlign: "center" },
  subtitle: { color: "#6b5c3e", textAlign: "center", marginBottom: "1.5rem", fontSize: "0.9rem" },
  form: { display: "flex", flexDirection: "column", gap: "0.75rem" },
  input: {
    background: "rgba(232,213,163,0.07)",
    border: "1px solid rgba(232,213,163,0.2)",
    borderRadius: 6,
    color: "#e8d5a3",
    padding: "0.65rem 0.9rem",
    fontSize: "1rem",
    outline: "none",
  },
  error: { color: "#e07070", fontSize: "0.85rem" },
  button: {
    background: "#b89b6a",
    color: "#0e0c09",
    border: "none",
    borderRadius: 6,
    padding: "0.7rem",
    fontSize: "1rem",
    cursor: "pointer",
    fontWeight: 500,
  },
};
