import { useState } from "react"

const COLORS = {
  blue:   { border: "#c8d8f0", dot: "#5b8fd4", label: "#3a6aaa" },
  amber:  { border: "#e8d4a0", dot: "#c89030", label: "#9a6c10" },
  purple: { border: "#d8c8e8", dot: "#9060c0", label: "#6a40a0" },
}

function Section({ color, label, children }) {
  const [open, setOpen] = useState(false)
  const c = COLORS[color]

  return (
    <div style={{ borderLeft: `2px solid ${c.border}`, paddingLeft: 12, marginBottom: 6 }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: "flex", alignItems: "center", gap: 7,
          background: "none", border: "none", cursor: "pointer",
          color: c.label, fontSize: 12,
          width: "100%", textAlign: "left",
          padding: "3px 0", fontFamily: "inherit",
        }}
      >
        <span style={{
          width: 6, height: 6, borderRadius: "50%",
          background: c.dot, flexShrink: 0,
        }} />
        <span style={{ flex: 1, fontWeight: 500 }}>{label}</span>
        <span style={{ fontSize: 9, color: "var(--muted)" }}>{open ? "▴" : "▾"}</span>
      </button>

      {open && (
        <div style={{
          marginTop: 6, fontSize: 13,
          color: "var(--text2)", lineHeight: 1.65,
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
    <div style={{ marginBottom: 18 }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          background: "none", border: "none", cursor: "pointer",
          display: "flex", alignItems: "center", gap: 5,
          fontSize: 12, color: "var(--muted)",
          fontFamily: "inherit", padding: "0 0 8px",
          transition: "color .15s",
        }}
        onMouseEnter={e => e.currentTarget.style.color = "var(--text2)"}
        onMouseLeave={e => e.currentTarget.style.color = "var(--muted)"}
      >
        <span style={{
          width: 5, height: 5, borderRadius: "50%",
          background: "var(--muted)", display: "inline-block",
        }} />
        {open ? "Hide inner process" : "See inner process"}
        <span style={{ fontSize: 9 }}>{open ? "▴" : "▾"}</span>
      </button>

      {open && (
        <div style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: "14px 16px",
          marginBottom: 20,
        }}>
          {profile && (
            <Section color="blue" label={`Seeker — ${profile.level} · ${profile.intent}`}>
              <div style={{ display: "grid", gridTemplateColumns: "70px 1fr", rowGap: 2 }}>
                <span style={{ color: "var(--muted)" }}>level</span><span>{profile.level}</span>
                <span style={{ color: "var(--muted)" }}>intent</span><span>{profile.intent}</span>
                <span style={{ color: "var(--muted)" }}>tone</span><span>{profile.emotional_tone}</span>
                <span style={{ color: "var(--muted)" }}>lang</span><span>{profile.language}</span>
              </div>
            </Section>
          )}

          <Section color="amber" label={`Agent A — Sanskrit${saQuery ? ` · ${saQuery}` : ""}`}>
            {aChunks.length > 0 && (
              <p style={{ color: "var(--muted)", marginBottom: 4 }}>
                Texts: {[...new Set(aChunks.map(c => c.text_name))].join(", ")}
              </p>
            )}
            {aText && (
              <p style={{
                fontFamily: "'Noto Sans Devanagari', sans-serif",
                fontSize: 13, color: "var(--text)", lineHeight: 1.7,
                whiteSpace: "pre-wrap", marginTop: 4,
              }}>{aText}</p>
            )}
          </Section>

          <Section color="amber" label="Agent B — Original Language">
            {bChunks.length > 0 && (
              <p style={{ color: "var(--muted)", marginBottom: 4 }}>
                Texts: {[...new Set(bChunks.map(c => c.text_name))].join(", ")}
              </p>
            )}
            {bText && (
              <p style={{ lineHeight: 1.7, whiteSpace: "pre-wrap", marginTop: 4 }}>{bText}</p>
            )}
          </Section>

          <Section color="purple" label={`Reflection${winner ? ` · Selected Agent ${winner.toUpperCase()}` : ""}`}>
            {reflText && (
              <p style={{ lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{reflText}</p>
            )}
          </Section>
        </div>
      )}
    </div>
  )
}
