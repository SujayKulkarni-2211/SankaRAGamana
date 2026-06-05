import ReactMarkdown from "react-markdown"

const DEVA_RE = /[ऀ-ॿ]/

function renderMixed(text) {
  if (!text) return null
  return text.split(/(\s+)/).map((part, i) =>
    DEVA_RE.test(part)
      ? <span key={i} style={{ fontFamily: "'Noto Sans Devanagari', sans-serif", fontSize: "1.02em" }}>{part}</span>
      : part
  )
}

const MD = {
  p: ({ children }) => <p style={{ marginBottom: "1.2em", lineHeight: 1.85 }}>{children}</p>,
  blockquote: ({ children }) => (
    <blockquote style={{
      borderLeft: "2px solid var(--saffron)", paddingLeft: "1.2em",
      margin: "1.2em 0", color: "var(--text2)", fontStyle: "italic",
    }}>{children}</blockquote>
  ),
  strong: ({ children }) => <strong style={{ fontWeight: 600, color: "var(--text)" }}>{children}</strong>,
  em: ({ children }) => <em style={{ fontStyle: "italic" }}>{children}</em>,
  code: ({ children }) => (
    <span style={{ fontFamily: "'Noto Sans Devanagari', sans-serif", color: "var(--saffron)", fontSize: "0.98em" }}>
      {children}
    </span>
  ),
}

export default function FinalResponse({ tokens, done }) {
  const text = tokens.join("")

  if (!text && !done) {
    return (
      <div style={{ display: "flex", gap: 5, padding: "16px 0 4px", alignItems: "center" }}>
        {[0, 1, 2].map(i => (
          <span key={i} style={{
            width: 7, height: 7, borderRadius: "50%",
            background: "var(--saffron)", display: "inline-block",
            animation: "sgpulse 1.4s ease-in-out infinite",
            animationDelay: `${i * 0.18}s`,
          }} />
        ))}
        <style>{`@keyframes sgpulse { 0%,100%{opacity:.25;transform:scale(.85)} 50%{opacity:1;transform:scale(1)} }`}</style>
      </div>
    )
  }

  const baseStyle = {
    fontSize: "1.06rem",
    lineHeight: 1.85,
    color: "var(--text)",
    wordBreak: "break-word",
    fontFamily: "'Crimson Pro', Georgia, serif",
  }

  if (!done) {
    return (
      <div style={baseStyle}>
        <p style={{ marginBottom: 0, lineHeight: 1.85, whiteSpace: "pre-wrap" }}>
          {renderMixed(text)}
          <span style={{
            display: "inline-block", width: 1.5, height: "1em",
            background: "var(--saffron)", verticalAlign: "text-bottom",
            animation: "sgblink 1s step-end infinite", marginLeft: 2,
          }} />
          <style>{`@keyframes sgblink { 50%{opacity:0} }`}</style>
        </p>
      </div>
    )
  }

  return (
    <div style={baseStyle}>
      <ReactMarkdown components={MD}>{text}</ReactMarkdown>
    </div>
  )
}
