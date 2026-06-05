import { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import ReactMarkdown from "react-markdown"
import ThinkingPanel from "../components/ThinkingPanel"
import Footer from "../components/Footer"

const MD = {
  p: ({ children }) => (
    <p style={{ marginBottom: "1.2em", lineHeight: 1.85 }}>{children}</p>
  ),
  blockquote: ({ children }) => (
    <blockquote style={{
      borderLeft: "2px solid var(--saffron)", paddingLeft: "1.2em",
      margin: "1.2em 0", color: "var(--text2)", fontStyle: "italic",
    }}>{children}</blockquote>
  ),
  strong: ({ children }) => <strong style={{ fontWeight: 600 }}>{children}</strong>,
}

export default function DarshanaView() {
  const { session_id } = useParams()
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!session_id) return
    fetch(`/api/conversation/${session_id}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [session_id])

  if (loading) return (
    <div style={{
      minHeight: "calc(100vh - 54px)",
      display: "flex", alignItems: "center", justifyContent: "center",
      color: "var(--muted)", fontSize: 15,
    }}>
      Loading…
    </div>
  )

  if (!data) return (
    <div style={{
      minHeight: "calc(100vh - 54px)",
      display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      textAlign: "center", gap: 10,
    }}>
      <p style={{
        fontFamily: "'Noto Sans Devanagari', sans-serif",
        fontSize: 28, color: "var(--muted)",
      }}>इदं नास्ति</p>
      <p style={{ fontSize: 15, color: "var(--muted)" }}>
        This darśana is not available.
      </p>
      <Link to="/" style={{ fontSize: 14, color: "var(--saffron)", textDecoration: "none", marginTop: 8 }}>
        ← Back to inquiry
      </Link>
    </div>
  )

  const events = {
    profile: data.seeker_profile,
    agent_a_translation: "",
    agent_a_response_tokens: data.agent_a_response ? [data.agent_a_response] : [],
    agent_b_response_tokens: data.agent_b_response ? [data.agent_b_response] : [],
    reflection_reasoning_tokens: data.reflection_reasoning ? [data.reflection_reasoning] : [],
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "calc(100vh - 54px)" }}>
      <main style={{ flex: 1, maxWidth: 680, width: "100%", margin: "0 auto", padding: "32px 24px 24px" }}>

        {/* Question bubble */}
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 20 }}>
          <p style={{
            background: "#fff",
            border: "1px solid var(--border)",
            borderRadius: "16px 16px 4px 16px",
            padding: "12px 18px",
            maxWidth: "70%",
            fontSize: 17,
            color: "var(--text)",
            lineHeight: 1.65,
            boxShadow: "0 1px 3px rgba(0,0,0,.06)",
          }}>
            {data.query}
          </p>
        </div>

        {/* Inner process */}
        <ThinkingPanel events={events} />

        {/* Response */}
        <div style={{
          fontSize: "1.06rem",
          lineHeight: 1.85,
          color: "var(--text)",
          fontFamily: "'Crimson Pro', Georgia, serif",
          wordBreak: "break-word",
        }}>
          <ReactMarkdown components={MD}>{data.final_response}</ReactMarkdown>
        </div>

        {/* Timestamp */}
        <p style={{ fontSize: 12, color: "var(--muted)", marginTop: 28, paddingTop: 16, borderTop: "1px solid var(--border)" }}>
          {new Date(data.created_at).toLocaleString(undefined, {
            dateStyle: "long", timeStyle: "short",
          })}
        </p>

        <Link
          to="/"
          style={{ display: "inline-block", marginTop: 12, fontSize: 13, color: "var(--saffron)", textDecoration: "none" }}
        >
          ← New inquiry
        </Link>
      </main>
      <Footer />
    </div>
  )
}
