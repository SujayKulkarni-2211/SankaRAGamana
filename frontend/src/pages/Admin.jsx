import React from "react";
import { useNavigate } from "react-router-dom";
import CorpusTracker from "../components/CorpusTracker";

export default function Admin() {
  const navigate = useNavigate();
  const [file, setFile] = React.useState(null);
  const [uploading, setUploading] = React.useState(false);
  const [uploadStatus, setUploadStatus] = React.useState("");

  function logout() {
    localStorage.removeItem("admin_token");
    navigate("/login");
  }

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setUploadStatus("Uploading...");
    const token = localStorage.getItem("admin_token");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch("/api/admin/upload", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const data = await res.json();
      setUploadStatus(res.ok ? `Done: ${JSON.stringify(data)}` : `Error: ${data.detail}`);
    } catch {
      setUploadStatus("Connection error");
    } finally {
      setUploading(false);
      setFile(null);
    }
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h2 style={styles.title}>Admin — SankaRĀGamana</h2>
        <button style={styles.logout} onClick={logout}>Logout</button>
      </header>

      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Upload Text</h3>
        <p style={styles.hint}>Accepted: .txt, .itx, .pdf, .json</p>
        <form onSubmit={handleUpload} style={styles.uploadForm}>
          <input
            type="file"
            accept=".txt,.itx,.pdf,.json"
            onChange={(e) => setFile(e.target.files[0])}
            style={styles.fileInput}
          />
          <button style={styles.button} type="submit" disabled={uploading || !file}>
            {uploading ? "Processing..." : "Upload & Ingest"}
          </button>
        </form>
        {uploadStatus && <p style={styles.status}>{uploadStatus}</p>}
      </section>

      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Corpus Tracker</h3>
        <CorpusTracker />
      </section>
    </div>
  );
}

const styles = {
  container: { maxWidth: 900, margin: "0 auto", padding: "1.5rem 1rem" },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "2rem",
    borderBottom: "1px solid rgba(232,213,163,0.15)",
    paddingBottom: "1rem",
  },
  title: { color: "#e8d5a3", fontSize: "1.4rem" },
  logout: {
    background: "transparent",
    border: "1px solid rgba(232,213,163,0.3)",
    color: "#b89b6a",
    borderRadius: 6,
    padding: "0.4rem 0.9rem",
    cursor: "pointer",
    fontSize: "0.9rem",
  },
  section: { marginBottom: "2.5rem" },
  sectionTitle: { color: "#e8d5a3", marginBottom: "0.75rem", fontSize: "1.1rem" },
  hint: { color: "#6b5c3e", fontSize: "0.85rem", marginBottom: "0.75rem" },
  uploadForm: { display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" },
  fileInput: { color: "#e8d5a3", background: "transparent", border: "none", fontSize: "0.9rem" },
  button: {
    background: "#b89b6a",
    color: "#0e0c09",
    border: "none",
    borderRadius: 6,
    padding: "0.55rem 1.2rem",
    cursor: "pointer",
    fontWeight: 500,
  },
  status: { marginTop: "0.75rem", color: "#b89b6a", fontSize: "0.9rem" },
};
