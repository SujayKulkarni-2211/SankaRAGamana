import { useState } from "react"

// The inner process, rendered like marginalia — a commentator's hand in the
// margin of a manuscript. Quiet, set aside, never competing with the response.

const SECTION = {
  seeker:     { rule: "#C9B89E", label: "var(--muted)" },
  agent:      { rule: "#D4A574", label: "var(--gold)" },
  reflection: { rule: "#C08A9E", label: "#9E5A6E" },
}

function Note({ kind, label, children }) {
  const [open, setOpen] = useState(false)
  const c = SECTION[kind]

  return (
    <div style={{
      borderLeft: `1.5px solid ${c.rule}`,
      paddingLeft: 14,
      marginBottom: 10,
    }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: "flex", alignItems: "center", gap: 8,
          background: "none", border: "none", cursor: "pointer",
          color: c.label, fontSize: 11.5,
          letterSpacing: "0.04em", textTransform: "uppercase",
          width: "100%", textAlign: "left",
          padding: "2px 0", fontFamily: "var(--font-body)",
        }}
      >
        <span style={{ flex: 1, fontWeight: 500 }}>{label}</span>
        <span style={{ fontSize: 9, color: "var(--muted)", opacity: 0.6 }}>
          {open ? "—" : "+"}
        </span>
      </button>

      {open && (
        <div style={{
          marginTop: 7, fontSize: 13.5,
          color: "var(--text2)", lineHeight: 1.7,
        }}>
          {children}
        </div>
      )}
    </div>
  )
}

export default function ThinkingPanel({ events }) {
  const [open, setOpen] = useState(false)

  const profile  = events.profile
  const saQuery  = events.agent_a_translation || ""
  const aChunks  = events.agent_a_chunks || []
  const aText    = (events.agent_a_response_tokens || []).join("")
  const bChunks  = events.agent_b_chunks || []
  const bText    = (events.agent_b_response_tokens || []).join("")
  const reflText = (events.reflection_reasoning_tokens || []).join("")
  const winner   = events.reflection_winner

  if (!profile && !saQuery && !aText && !bText && !reflText) return null

  return (
    <div style={{ marginBottom: 22 }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          background: "none", border: "none", cursor: "pointer",
          display: "flex", alignItems: "center", gap: 7,
          fontSize: 11.5, color: "var(--muted)",
          fontFamily: "var(--font-body)", padding: "0 0 6px",
          letterSpacing: "0.03em", fontStyle: "italic",
          transition: "color .2s",
        }}
        onMouseEnter={e => e.currentTarget.style.color = "var(--text2)"}
        onMouseLeave={e => e.currentTarget.style.color = "var(--muted)"}
      >
        <span style={{ fontSize: 13, opacity: 0.7 }}>{open ? "❧" : "❧"}</span>
        {open ? "hide the inner process" : "the inner process"}
      </button>

      {open && (
        <div style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 4,
          padding: "18px 20px",
          marginTop: 4, marginBottom: 6,
          boxShadow: "0 1px 2px rgba(43,32,24,0.04)",
        }}>
          {profile && (
            <Note kind="seeker" label={`Seeker · ${profile.level} · ${profile.intent}`}>
              <div style={{ display: "grid", gridTemplateColumns: "64px 1fr", rowGap: 3, fontSize: 13 }}>
                <span style={{ color: "var(--muted)" }}>level</span><span>{profile.level}</span>
                <span style={{ color: "var(--muted)" }}>intent</span><span>{profile.intent}</span>
                <span style={{ color: "var(--muted)" }}>tone</span><span>{profile.emotional_tone}</span>
                <span style={{ color: "var(--muted)" }}>language</span><span>{profile.language}</span>
              </div>
            </Note>
          )}

          <Note kind="agent" label={`Through Sanskrit${saQuery ? ` · ${saQuery}` : ""}`}>
            {aChunks.length > 0 && (
              <p style={{ color: "var(--muted)", marginBottom: 6, fontSize: 12, fontStyle: "italic" }}>
                from {[...new Set(aChunks.map(c => c.text_name))].join(", ")}
              </p>
            )}
            {aText && (
              <p className="deva" style={{
                fontSize: 14.5, color: "var(--text)", lineHeight: 1.85,
                whiteSpace: "pre-wrap", marginTop: 4, fontStyle: "normal",
              }}>{aText}</p>
            )}
          </Note>

          <Note kind="agent" label="In the seeker's tongue">
            {bChunks.length > 0 && (
              <p style={{ color: "var(--muted)", marginBottom: 6, fontSize: 12, fontStyle: "italic" }}>
                from {[...new Set(bChunks.map(c => c.text_name))].join(", ")}
              </p>
            )}
            {bText && (
              <p style={{ lineHeight: 1.75, whiteSpace: "pre-wrap", marginTop: 4 }}>{bText}</p>
            )}
          </Note>

          <Note kind="reflection" label={`Reflection${winner ? ` · chose ${winner.toUpperCase()}` : ""}`}>
            {reflText && (
              <p style={{ lineHeight: 1.75, whiteSpace: "pre-wrap", fontStyle: "italic" }}>{reflText}</p>
            )}
          </Note>
        </div>
      )}
    </div>
  )
}
