import ReactMarkdown from "react-markdown"

const DEVA_RE = /[ऀ-ॿ]/

// Is this line predominantly Devanagari? (a verse line, regardless of whether
// it ends in a daṇḍa — fixes the "line 1 big, line 2 small" inconsistency)
function isVerseLine(t) {
  if (!t.trim()) return false
  const deva = (t.match(/[ऀ-ॿ]/g) || []).length
  const latin = (t.match(/[A-Za-z]/g) || []).length
  return deva >= 4 && deva > latin
}

// Inline mixed text: wrap Devanagari runs in the manuscript face.
function renderMixed(text) {
  if (!text) return null
  return text.split(/(\s+)/).map((part, i) =>
    DEVA_RE.test(part)
      ? <span key={i} className="deva">{part}</span>
      : part
  )
}

// A śloka block — ALL lines rendered at one consistent size, centered, set
// apart like verse on a manuscript page with a faint marginal rule.
function Verse({ lines }) {
  return (
    <div style={{
      margin: "var(--space-md) 0",
      paddingLeft: "var(--space-md)",
      borderLeft: "2px solid var(--flame)",
    }}>
      {lines.map((ln, i) => (
        <div
          key={i}
          className="deva"
          style={{
            fontSize: "1.34rem",
            lineHeight: 1.95,
            color: "var(--ink)",
            letterSpacing: "0.012em",
          }}
        >
          {ln.trim()}
        </div>
      ))}
    </div>
  )
}

const MD = {
  p: ({ children }) => (
    <p style={{ marginBottom: "1.15em", lineHeight: 1.88 }}>{children}</p>
  ),
  blockquote: ({ children }) => (
    <blockquote style={{
      borderLeft: "2px solid var(--brass)",
      paddingLeft: "1.3em",
      margin: "1.3em 0",
      color: "var(--ink-soft)",
      fontStyle: "italic",
    }}>{children}</blockquote>
  ),
  strong: ({ children }) => (
    <strong style={{ fontWeight: 600, color: "var(--ink)" }}>{children}</strong>
  ),
  em: ({ children }) => <em style={{ fontStyle: "italic" }}>{children}</em>,
  code: ({ children }) => (
    <span className="deva" style={{ color: "var(--flame-2)" }}>{children}</span>
  ),
}

// Group consecutive verse-lines into one Verse block; everything else is prose.
function renderCompleted(text) {
  const blocks = text.split("\n\n")
  const out = []

  blocks.forEach((block, bi) => {
    const lines = block.split("\n")
    let proseBuf = []
    let verseBuf = []

    const flushProse = () => {
      if (proseBuf.length) {
        out.push(
          <ReactMarkdown key={`p-${bi}-${out.length}`} components={MD}>
            {proseBuf.join("\n")}
          </ReactMarkdown>
        )
        proseBuf = []
      }
    }
    const flushVerse = () => {
      if (verseBuf.length) {
        out.push(<Verse key={`v-${bi}-${out.length}`} lines={verseBuf} />)
        verseBuf = []
      }
    }

    for (const line of lines) {
      if (isVerseLine(line)) {
        flushProse()
        verseBuf.push(line)
      } else {
        flushVerse()
        proseBuf.push(line)
      }
    }
    flushVerse()
    flushProse()
  })

  return out
}

export default function FinalResponse({ tokens, done }) {
  const text = tokens.join("")

  // Thinking — a single flame breathing.
  if (!text && !done) {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 13, padding: "22px 0 6px" }}>
        <span style={{
          width: 9, height: 12,
          borderRadius: "50% 50% 50% 50% / 62% 62% 38% 38%",
          background: "linear-gradient(180deg,#E0691B,#C8431C)",
          display: "inline-block",
          animation: "flamebreath 1.8s ease-in-out infinite",
          boxShadow: "0 0 11px rgba(200,67,28,.42)",
        }} />
        <span className="mono" style={{
          fontSize: ".74rem", letterSpacing: ".08em", textTransform: "uppercase",
          color: "var(--ink-faint)",
        }}>
          consulting the texts
        </span>
      </div>
    )
  }

  const base = {
    fontSize: "1.08rem",
    lineHeight: 1.88,
    color: "var(--ink)",
    wordBreak: "break-word",
    fontFamily: "var(--font-body)",
  }

  // Streaming — ink settling, plain with a flame cursor.
  if (!done) {
    return (
      <div style={{ ...base, animation: "inkrise .5s var(--ease-ink)" }}>
        <p style={{ marginBottom: 0, lineHeight: 1.88, whiteSpace: "pre-wrap" }}>
          {renderMixed(text)}
          <span style={{
            display: "inline-block", width: 2, height: "1.05em",
            background: "var(--flame)", verticalAlign: "text-bottom",
            animation: "flamebreath 1.4s ease-in-out infinite",
            marginLeft: 3, borderRadius: 1,
          }} />
        </p>
      </div>
    )
  }

  // Settled — verse/prose distinction, consistent Devanagari sizing.
  return (
    <div style={{ ...base, animation: "inkrise .6s var(--ease-ink)" }}>
      {renderCompleted(text)}
    </div>
  )
}
