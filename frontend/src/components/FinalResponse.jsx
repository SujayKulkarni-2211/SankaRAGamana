import ReactMarkdown from "react-markdown"

const DEVA_RE = /[ऀ-ॿ]/
// A "verse line" heuristic: a line that is mostly Devanagari and ends in a
// daṇḍa (। or ॥) — rendered as a centered verse, not flowing prose.
const VERSE_LINE = /[।॥]\s*$/

// Split mixed text into inline spans, wrapping Devanagari runs in the
// manuscript Devanagari face so conjuncts render beautifully and large.
function renderMixed(text) {
  if (!text) return null
  return text.split(/(\s+)/).map((part, i) =>
    DEVA_RE.test(part)
      ? <span key={i} className="deva" style={{ fontStyle: "normal" }}>{part}</span>
      : part
  )
}

// A Sanskrit verse — centered, larger, set apart like a śloka on the page.
function Verse({ children }) {
  return (
    <div style={{
      textAlign: "center",
      margin: "1.6em 0",
      padding: "0.2em 0",
    }}>
      <span className="deva" style={{
        fontSize: "1.42rem",
        color: "var(--text)",
        lineHeight: 2.05,
        letterSpacing: "0.01em",
      }}>
        {children}
      </span>
    </div>
  )
}

const MD = {
  p: ({ children }) => (
    <p style={{ marginBottom: "1.25em", lineHeight: 1.92 }}>{children}</p>
  ),
  blockquote: ({ children }) => (
    <blockquote style={{
      borderLeft: "2px solid var(--saffron)",
      paddingLeft: "1.3em",
      margin: "1.4em 0",
      color: "var(--text2)",
      fontStyle: "italic",
    }}>{children}</blockquote>
  ),
  strong: ({ children }) => (
    <strong style={{ fontWeight: 600, color: "var(--text)" }}>{children}</strong>
  ),
  em: ({ children }) => <em style={{ fontStyle: "italic" }}>{children}</em>,
  code: ({ children }) => (
    <span className="deva" style={{ color: "var(--saffron2)", fontStyle: "normal" }}>
      {children}
    </span>
  ),
}

// Render the completed response with verse/prose distinction.
// Devanagari verse lines (ending in daṇḍa) become centered Verses;
// everything else flows as manuscript prose via markdown.
function renderCompleted(text) {
  const blocks = text.split("\n\n")
  return blocks.map((block, bi) => {
    const lines = block.split("\n")
    const out = []
    let proseBuf = []

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

    for (const line of lines) {
      const t = line.trim()
      const devaCount = (t.match(/[ऀ-ॿ]/g) || []).length
      const isVerse = t && VERSE_LINE.test(t) && devaCount > t.length * 0.4
      if (isVerse) {
        flushProse()
        out.push(<Verse key={`v-${bi}-${out.length}`}>{renderMixed(t)}</Verse>)
      } else {
        proseBuf.push(line)
      }
    }
    flushProse()
    return <div key={bi}>{out}</div>
  })
}

export default function FinalResponse({ tokens, done }) {
  const text = tokens.join("")

  // Thinking state — a single flame breathing, not three machine dots.
  if (!text && !done) {
    return (
      <div style={{
        display: "flex", alignItems: "center", gap: 12,
        padding: "20px 0 6px",
      }}>
        <span style={{
          width: 9, height: 11, borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%",
          background: "var(--saffron)",
          display: "inline-block",
          animation: "flamebreath 1.8s ease-in-out infinite",
          boxShadow: "0 0 10px rgba(192,69,27,0.4)",
        }} />
        <span style={{ fontSize: "0.92rem", color: "var(--muted)", fontStyle: "italic", letterSpacing: "0.02em" }}>
          consulting the texts…
        </span>
      </div>
    )
  }

  const baseStyle = {
    fontSize: "1.08rem",
    lineHeight: 1.92,
    color: "var(--text)",
    wordBreak: "break-word",
    fontFamily: "var(--font-body)",
  }

  // Streaming — plain text settling in with a soft cursor, ink-on-paper.
  if (!done) {
    return (
      <div style={{ ...baseStyle, animation: "inkrise 0.5s ease-out" }}>
        <p style={{ marginBottom: 0, lineHeight: 1.92, whiteSpace: "pre-wrap" }}>
          {renderMixed(text)}
          <span style={{
            display: "inline-block", width: 2, height: "1.05em",
            background: "var(--saffron)", verticalAlign: "text-bottom",
            animation: "flamebreath 1.4s ease-in-out infinite", marginLeft: 3,
            borderRadius: 1,
          }} />
        </p>
      </div>
    )
  }

  // Completed — verse/prose distinction, settled in.
  return (
    <div style={{ ...baseStyle, animation: "inkrise 0.6s ease-out" }}>
      {renderCompleted(text)}
    </div>
  )
}
