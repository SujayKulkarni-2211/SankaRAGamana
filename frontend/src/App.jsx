import { useState, useEffect } from "react"
import { BrowserRouter, Routes, Route, Link, useNavigate, useLocation } from "react-router-dom"
import Chat from "./pages/Chat"
import About from "./pages/About"
import History from "./pages/History"
import { getUser, onAuthStateChange, signInWithGoogle, signOut } from "./lib/supabase"

function GoogleIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" style={{ flexShrink: 0 }}>
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
  )
}

function Avatar({ user }) {
  // Try multiple places Supabase puts the avatar
  const url =
    user?.user_metadata?.avatar_url ||
    user?.user_metadata?.picture ||
    user?.identities?.[0]?.identity_data?.avatar_url ||
    null

  const name =
    user?.user_metadata?.full_name ||
    user?.user_metadata?.name ||
    user?.email?.split("@")[0] ||
    "U"

  const initials = name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase()

  if (url) {
    return (
      <img
        src={url}
        alt={name}
        referrerPolicy="no-referrer"
        style={{
          width: 28, height: 28, borderRadius: "50%",
          border: "1.5px solid var(--border2)",
          objectFit: "cover",
          flexShrink: 0,
        }}
        onError={e => { e.target.style.display = "none"; e.target.nextSibling.style.display = "flex" }}
      />
    )
  }

  // Fallback initials circle
  return (
    <span style={{
      width: 28, height: 28, borderRadius: "50%",
      background: "var(--border2)",
      border: "1.5px solid var(--border2)",
      display: "flex", alignItems: "center", justifyContent: "center",
      fontSize: 11, fontWeight: 600, color: "var(--text2)",
      flexShrink: 0, fontFamily: "system-ui, sans-serif",
    }}>
      {initials}
    </span>
  )
}

const TRANSLATE_LANGS = [
  { code: "", label: "Original" },
  { code: "hi", label: "हिन्दी" },
  { code: "kn", label: "ಕನ್ನಡ" },
  { code: "ta", label: "தமிழ்" },
  { code: "te", label: "తెలుగు" },
  { code: "ml", label: "മലയാളം" },
  { code: "mr", label: "मराठी" },
  { code: "bn", label: "বাংলা" },
  { code: "sa", label: "संस्कृत" },
  { code: "fr", label: "Français" },
  { code: "de", label: "Deutsch" },
  { code: "es", label: "Español" },
  { code: "ja", label: "日本語" },
  { code: "zh-CN", label: "中文" },
  { code: "ar", label: "العربية" },
  { code: "ru", label: "Русский" },
]

function TranslateButton({ current, onChange }) {
  const [open, setOpen] = useState(false)

  function pick(code) {
    setOpen(false)
    onChange(code)
    if (code === "") {
      window.resetTranslate?.()
    } else {
      window.doGTranslate?.(`en|${code}`)
    }
  }

  const label = TRANSLATE_LANGS.find(l => l.code === current)?.label || "Translate"

  return (
    <div style={{ position: "relative" }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: "flex", alignItems: "center", gap: 5,
          fontSize: 13, color: current ? "var(--saffron)" : "var(--muted)",
          background: "none",
          border: `1px solid ${current ? "var(--saffron)" : "var(--border2)"}`,
          borderRadius: 6, padding: "4px 10px",
          cursor: "pointer", fontFamily: "inherit",
          transition: "all .15s",
        }}
        onMouseEnter={e => { if (!current) { e.currentTarget.style.borderColor = "var(--saffron)"; e.currentTarget.style.color = "var(--saffron)" }}}
        onMouseLeave={e => { if (!current) { e.currentTarget.style.borderColor = "var(--border2)"; e.currentTarget.style.color = "var(--muted)" }}}
      >
        <GlobeIcon />
        {current ? label : "Translate"}
      </button>

      {open && (
        <>
          <div style={{ position: "fixed", inset: 0, zIndex: 40 }} onClick={() => setOpen(false)} />
          <div style={{
            position: "absolute", top: "calc(100% + 6px)", right: 0, zIndex: 50,
            background: "var(--surface)", border: "1px solid var(--border2)",
            borderRadius: 8, boxShadow: "0 4px 20px rgba(0,0,0,.10)",
            padding: "6px 0", minWidth: 150,
            display: "grid", gridTemplateColumns: "1fr 1fr",
          }}>
            {TRANSLATE_LANGS.map(l => (
              <button
                key={l.code}
                onClick={() => pick(l.code)}
                style={{
                  padding: "7px 14px", fontSize: 13, textAlign: "left",
                  background: l.code === current ? "var(--bg2)" : "none",
                  border: "none", cursor: "pointer",
                  color: l.code === current ? "var(--saffron)" : "var(--text2)",
                  fontFamily: "inherit", transition: "background .1s",
                  whiteSpace: "nowrap",
                }}
                onMouseEnter={e => { if (l.code !== current) e.currentTarget.style.background = "var(--bg2)" }}
                onMouseLeave={e => { if (l.code !== current) e.currentTarget.style.background = "none" }}
              >
                {l.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function GlobeIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
    </svg>
  )
}

function Header({ user, onNewChat, displayLang, onLangChange }) {
  const navigate   = useNavigate()
  const location   = useLocation()
  const isChat     = location.pathname === "/" || location.pathname.startsWith("/darshana")

  return (
    <header className="notranslate" style={{
      position: "sticky", top: 0, zIndex: 50,
      height: 54,
      background: "var(--header)",
      borderBottom: "1px solid var(--border)",
      display: "flex", alignItems: "center",
      justifyContent: "space-between",
      padding: "0 28px",
    }}>
      {/* Logo */}
      <Link to="/" style={{
        fontFamily: "'Crimson Pro', Georgia, serif",
        fontSize: 19, fontWeight: 600,
        color: "var(--text)", textDecoration: "none",
        letterSpacing: "-0.01em",
      }}>
        SankaR<span style={{ color: "var(--saffron)" }}>Ā</span>Gamana
      </Link>

      {/* Nav */}
      <nav style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <TranslateButton current={displayLang} onChange={onLangChange} />
        {isChat && (
          <button
            onClick={onNewChat}
            style={{
              fontSize: 13, color: "var(--text2)",
              background: "none",
              border: "1px solid var(--border2)",
              borderRadius: 6, padding: "4px 12px",
              cursor: "pointer", fontFamily: "inherit",
              display: "flex", alignItems: "center", gap: 4,
              transition: "all .15s",
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--saffron)"; e.currentTarget.style.color = "var(--saffron)" }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--border2)"; e.currentTarget.style.color = "var(--text2)" }}
          >
            <span style={{ fontSize: 15, lineHeight: 1 }}>+</span> New
          </button>
        )}

        <NavLink to="/about">About</NavLink>

        {user ? (
          <>
            <NavLink to="/history">My Darśanas</NavLink>
            <button
              onClick={() => signOut().then(() => { navigate("/"); window.location.reload() })}
              style={{
                fontSize: 13, color: "var(--muted)", background: "none",
                border: "none", cursor: "pointer", fontFamily: "inherit",
                padding: "4px 8px", borderRadius: 4,
                transition: "color .15s",
              }}
              onMouseEnter={e => e.currentTarget.style.color = "var(--text)"}
              onMouseLeave={e => e.currentTarget.style.color = "var(--muted)"}
            >Sign out</button>
            <Avatar user={user} />
          </>
        ) : (
          <button
            onClick={signInWithGoogle}
            style={{
              display: "flex", alignItems: "center", gap: 6,
              fontSize: 13, color: "var(--text2)",
              background: "none",
              border: "1px solid var(--border2)",
              borderRadius: 6, padding: "5px 14px",
              cursor: "pointer", fontFamily: "inherit",
              transition: "all .15s",
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--saffron)"; e.currentTarget.style.color = "var(--saffron)" }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--border2)"; e.currentTarget.style.color = "var(--text2)" }}
          >
            <GoogleIcon />
            Sign in with Google
          </button>
        )}
      </nav>
    </header>
  )
}

function NavLink({ to, children }) {
  return (
    <Link
      to={to}
      style={{
        fontSize: 13, color: "var(--muted)",
        textDecoration: "none", padding: "4px 8px",
        borderRadius: 4, transition: "color .15s",
        fontFamily: "'Crimson Pro', Georgia, serif",
      }}
      onMouseEnter={e => e.currentTarget.style.color = "var(--text)"}
      onMouseLeave={e => e.currentTarget.style.color = "var(--muted)"}
    >
      {children}
    </Link>
  )
}

function AppInner() {
  const [user,        setUser]        = useState(null)
  const [chatKey,     setChatKey]     = useState(0)
  const [displayLang, setDisplayLang] = useState("")  // "" = original English
  const navigate = useNavigate()

  useEffect(() => {
    getUser().then(setUser)
    const { data } = onAuthStateChange(setUser)
    return () => data?.subscription?.unsubscribe()
  }, [])

  function newChat() {
    setChatKey(k => k + 1)
    navigate("/")
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Header user={user} onNewChat={newChat} displayLang={displayLang} onLangChange={setDisplayLang} />
      <div style={{ flex: 1 }}>
        <Routes>
          <Route path="/"                    element={<Chat key={`new-${chatKey}`} user={user} displayLang={displayLang} />} />
          <Route path="/darshana/:session_id" element={<Chat key={`darshana-${chatKey}`} user={user} displayLang={displayLang} />} />
          <Route path="/about"              element={<About />} />
          <Route path="/history"            element={<History user={user} />} />
        </Routes>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppInner />
    </BrowserRouter>
  )
}
