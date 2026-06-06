export default function Footer() {
  return (
    <footer style={{
      textAlign: "center",
      padding: "24px 16px 28px",
      borderTop: "1px solid var(--border)",
      background: "var(--header)",
      display: "flex", flexDirection: "column", gap: 8,
    }}>
      <p style={{ fontSize: 12.5, color: "var(--muted)", letterSpacing: "0.01em" }}>
        Data:{" "}
        <A href="https://sanskritdocuments.org">sanskritdocuments.org</A>
        {" · "}
        <A href="https://gretil.sub.uni-goettingen.de">GRETIL</A>
      </p>

      <p style={{ fontSize: 12.5, color: "var(--muted)", display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
        <GithubIcon />
        <A href="https://github.com/SujayKulkarni-2211/SankaRAGamana">SankaRĀGamana</A>
      </p>

      <p style={{ fontSize: 12, color: "var(--muted)", opacity: 0.85, fontStyle: "italic", marginTop: 2 }}>
        <A href="https://sujaykulkarni-2211.github.io/sujayvkresume/cosmos.html" dim>
          Built by the grace of Ādi Śaṅkara and Devī Sarasvatī by Sujay V Kulkarni
        </A>
      </p>
    </footer>
  )
}

function A({ href, children, dim }) {
  return (
    <a
      href={href} target="_blank" rel="noreferrer"
      style={{
        color: "var(--muted)",
        textDecoration: dim ? "none" : "underline",
        textDecorationColor: "var(--border2)",
        textUnderlineOffset: "2px",
        transition: "color .15s",
      }}
      onMouseEnter={e => e.currentTarget.style.color = "var(--saffron)"}
      onMouseLeave={e => e.currentTarget.style.color = "var(--muted)"}
    >
      {children}
    </a>
  )
}

function GithubIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="var(--muted)">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 21.795 24 17.295 24 12c0-6.63-5.37-12-12-12"/>
    </svg>
  )
}
