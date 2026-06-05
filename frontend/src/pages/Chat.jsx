import { useState, useRef, useEffect, useCallback } from "react"
import { useParams, useNavigate, useLocation } from "react-router-dom"
import ThinkingPanel from "../components/ThinkingPanel"
import FinalResponse from "../components/FinalResponse"
import Feedback from "../components/Feedback"
import Footer from "../components/Footer"
import { signInWithGoogle } from "../lib/supabase"

const PLACEHOLDERS = ["अथातो ब्रह्म जिज्ञासा…", "Ask Śaṅkarācārya…", "ಶಂಕರರನ್ನು ಕೇಳಿ…"]

// Script-range detectors — fast, no API call needed
const DEVA_RE    = /[ऀ-ॿ]/       // Sanskrit / Hindi / Marathi
const KANNADA_RE = /[ಀ-೿]/       // Kannada
const TAMIL_RE   = /[஀-௿]/       // Tamil
const TELUGU_RE  = /[ఀ-౿]/       // Telugu
const MALAYALAM_RE = /[ഀ-ൿ]/     // Malayalam
const ARABIC_RE  = /[؀-ۿ]/ // Arabic
const CJK_RE     = /[一-鿿぀-ヿ]/ // Chinese / Japanese
const CYRILLIC_RE = /[Ѐ-ӿ]/ // Russian
// Latin-script non-English heuristic — if majority chars are latin but has
// accented chars common in French/German/Spanish
const LATIN_ACCENT_RE = /[àáâãäåæçèéêëìíîïðñòóôõöùúûüýþßœ]/i

const ASK_LABEL  = { en: "Ask", sa: "पृच्छ", kn: "ಕೇಳಿ" }

function detectScript(t) {
  if (DEVA_RE.test(t))       return "non-en"
  if (KANNADA_RE.test(t))    return "non-en"
  if (TAMIL_RE.test(t))      return "non-en"
  if (TELUGU_RE.test(t))     return "non-en"
  if (MALAYALAM_RE.test(t))  return "non-en"
  if (ARABIC_RE.test(t))     return "non-en"
  if (CJK_RE.test(t))        return "non-en"
  if (CYRILLIC_RE.test(t))   return "non-en"
  if (LATIN_ACCENT_RE.test(t)) return "non-en"
  return "en"
}

function detectLang(t) {
  if (DEVA_RE.test(t))    return "sa"
  if (KANNADA_RE.test(t)) return "kn"
  return "en"
}

// Translate any text to English via our backend — used for input normalisation
async function toEnglish(text) {
  try {
    const r = await fetch("/api/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, target: "en" }),
    })
    const d = await r.json()
    return d.translated || text
  } catch {
    return text
  }
}

// ─── Sign-in modal ────────────────────────────────────────────────────────────
function SignInModal({ onClose }) {
  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 100,
      background: "rgba(26,18,8,0.60)",
      backdropFilter: "blur(8px)",
      display: "flex", alignItems: "center", justifyContent: "center",
    }} onClick={onClose}>
      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border2)",
          borderRadius: 14,
          padding: "36px 40px",
          maxWidth: 380, width: "90%",
          boxShadow: "0 8px 40px rgba(0,0,0,.12)",
          textAlign: "center",
        }}
        onClick={e => e.stopPropagation()}
      >
        <p style={{
          fontFamily: "'Noto Sans Devanagari', sans-serif",
          fontSize: 22, color: "var(--saffron)",
          marginBottom: 6,
        }}>अथातो ब्रह्म जिज्ञासा</p>
        <p style={{ fontSize: 18, color: "var(--text)", marginBottom: 8, fontWeight: 600 }}>
          Continue your inquiry
        </p>
        <p style={{ fontSize: 15, color: "var(--text2)", lineHeight: 1.65, marginBottom: 28 }}>
          Sign in to save your darśanas, continue conversations, and receive 3 questions per hour.
          Without signing in, one question is allowed per hour — tracked by your network address,
          not your browser, so clearing history or opening new tabs will not change this.
        </p>
        <button
          onClick={signInWithGoogle}
          style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            gap: 10, width: "100%",
            background: "var(--saffron)", color: "#fff",
            border: "none", borderRadius: 9,
            padding: "13px 20px", fontSize: 16,
            fontFamily: "'Crimson Pro', Georgia, serif",
            fontWeight: 600, cursor: "pointer",
            transition: "background .15s",
          }}
          onMouseEnter={e => e.currentTarget.style.background = "var(--saffron2)"}
          onMouseLeave={e => e.currentTarget.style.background = "var(--saffron)"}
        >
          <GoogleIcon />
          Sign in with Google
        </button>
        <button
          onClick={onClose}
          style={{
            marginTop: 14, fontSize: 13, color: "var(--muted)",
            background: "none", border: "none", cursor: "pointer",
            fontFamily: "inherit",
          }}
        >Continue without signing in</button>
      </div>
    </div>
  )
}

function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24">
      <path fill="#fff" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path fill="#fff" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path fill="#fff" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
      <path fill="#fff" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
  )
}

// ─── Exchange ─────────────────────────────────────────────────────────────────
function Exchange({ ex }) {
  return (
    <article style={{ marginBottom: 40 }}>
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 20 }}>
        <p style={{
          background: "var(--surface)", border: "1px solid var(--border2)",
          borderRadius: "16px 16px 4px 16px",
          padding: "12px 18px", maxWidth: "70%",
          fontSize: 17, color: "var(--text)", lineHeight: 1.65,
          boxShadow: "0 2px 8px rgba(0,0,0,.06)",
        }}>{ex.question}</p>
      </div>

      {ex.rateLimited ? (
        <div style={{
          background: "var(--surface)", border: "1px solid var(--border2)",
          borderRadius: 10, padding: "24px 28px",
          borderLeft: "3px solid var(--saffron)",
        }}>
          <p style={{ fontSize: 17, color: "var(--text2)", lineHeight: 1.75, marginBottom: 12 }}>
            {ex.rateLimited.message}
          </p>
          {ex.rateLimited.reset_at && (
            <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 8 }}>
              Resets at {new Date(ex.rateLimited.reset_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </p>
          )}
          <a href="https://github.com/SujayKulkarni-2211/SankaRAGamana"
            target="_blank" rel="noreferrer"
            style={{ fontSize: 13, color: "var(--saffron)", textDecoration: "none" }}>
            View source on GitHub →
          </a>
        </div>
      ) : (
        <div>
          <ThinkingPanel events={ex.events} />
          <FinalResponse tokens={ex.finalTokens} done={ex.done} />
          {ex.error && <p style={{ fontSize: 14, color: "var(--muted)", marginTop: 8 }}>{ex.error}</p>}
          {ex.done && ex.conversationData && <Feedback conversationData={ex.conversationData} />}
        </div>
      )}
    </article>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────
export default function Chat({ user, displayLang }) {
  const { session_id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const isDarshanaRoute = location.pathname.startsWith("/darshana/")
  const [input,       setInput]       = useState("")
  const [exchanges,   setExchanges]   = useState([])
  const [streaming,   setStreaming]   = useState(false)
  const [phIdx,       setPhIdx]       = useState(0)
  // Show modal on entry for anonymous users
  const [showSignIn, setShowSignIn] = useState(!user)
  useEffect(() => { if (user) setShowSignIn(false) }, [user])
  // history = [{role, content}] pairs sent to backend for context
  const [history,     setHistory]     = useState([])
  const textareaRef = useRef()
  const feedRef     = useRef()
  const lang        = detectLang(input)

  // Clear state when navigating to /
  useEffect(() => {
    if (!isDarshanaRoute) {
      setExchanges([])
      setHistory([])
      setInput("")
    }
  }, [isDarshanaRoute])

  // Load saved conversation only when actually on /darshana/:session_id
  useEffect(() => {
    if (!session_id || !isDarshanaRoute) return
    fetch(`/api/conversation/${session_id}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return
        // Reconstruct exchanges from saved conversation
        const saved = {
          id: Date.now(),
          question: data.query,
          events: {
            profile: data.seeker_profile,
            agent_a_response_tokens: data.agent_a_response ? [data.agent_a_response] : [],
            agent_b_response_tokens: data.agent_b_response ? [data.agent_b_response] : [],
            reflection_reasoning_tokens: data.reflection_reasoning ? [data.reflection_reasoning] : [],
          },
          finalTokens: [data.final_response],
          done: true,
          rateLimited: null,
          error: null,
          conversationData: null,
        }
        setExchanges([saved])
        // Seed history so follow-up questions have context
        setHistory([
          { role: "user",      content: data.query },
          { role: "assistant", content: data.final_response },
        ])
      })
  }, [session_id])

  // Placeholder rotation
  useEffect(() => {
    const t = setInterval(() => setPhIdx(i => (i + 1) % PLACEHOLDERS.length), 3500)
    return () => clearInterval(t)
  }, [])

  // Auto-scroll
  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight
  }, [exchanges])

  function handleInput(e) {
    setInput(e.target.value)
    e.target.style.height = "auto"
    e.target.style.height = Math.min(e.target.scrollHeight, 180) + "px"
  }

  const submit = useCallback(async () => {
    const q = input.trim()
    if (!q || streaming) return

    // Anonymous users: one free question after dismissing modal, then block
    if (!user && exchanges.length >= 1) {
      setShowSignIn(true)
      return
    }

    setInput("")
    if (textareaRef.current) textareaRef.current.style.height = "auto"
    setStreaming(true)

    // Always send English to agents — translate if input is non-English script
    // or if user has a non-English display language selected
    let agentQuery = q
    if (detectScript(q) === "non-en" || (displayLang && displayLang !== "en")) {
      agentQuery = await toEnglish(q)
    }

    const id = Date.now()
    setExchanges(prev => [...prev, {
      id, question: q, events: {}, finalTokens: [],   // show original in bubble
      done: false, rateLimited: null, error: null, conversationData: null,
    }])

    try {
      const res = await fetch("/api/query/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: agentQuery,
          user_id:  user?.id ?? null,
          history:  history,
        }),
      })

      const reader  = res.body.getReader()
      const decoder = new TextDecoder()
      let buf = ""
      let finalText = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const parts = buf.split("\n\n")
        buf = parts.pop()

        for (const part of parts) {
          if (!part.trim()) continue
          let event = "", data = ""
          for (const line of part.split("\n")) {
            if (line.startsWith("event:")) event = line.slice(6).trim()
            // SSE spec: strip exactly ONE optional leading space after "data:".
            // Do NOT trim — text-token events (final_response, agent_*) carry
            // meaningful leading/trailing spaces between word chunks.
            if (line.startsWith("data:")) {
              data = line.slice(5)
              if (data.startsWith(" ")) data = data.slice(1)
            }
          }
          if (!event) continue

          setExchanges(prev => prev.map(ex => {
            if (ex.id !== id) return ex
            switch (event) {
              case "rate_limited":
                return { ...ex, rateLimited: JSON.parse(data), done: true }
              case "profile":
                return { ...ex, events: { ...ex.events, profile: JSON.parse(data) } }
              case "agent_a_translation":
                return { ...ex, events: { ...ex.events, agent_a_translation: data } }
              case "agent_a_chunks":
                return { ...ex, events: { ...ex.events, agent_a_chunks: JSON.parse(data) } }
              case "agent_a_response":
                return { ...ex, events: { ...ex.events, agent_a_response_tokens: [...(ex.events.agent_a_response_tokens||[]), data] } }
              case "agent_b_chunks":
                return { ...ex, events: { ...ex.events, agent_b_chunks: JSON.parse(data) } }
              case "agent_b_response":
                return { ...ex, events: { ...ex.events, agent_b_response_tokens: [...(ex.events.agent_b_response_tokens||[]), data] } }
              case "reflection_reasoning": {
                let r = data
                try { r = JSON.parse(data) } catch { /* fallback */ }
                return { ...ex, events: { ...ex.events, reflection_reasoning_tokens: [r] } }
              }
              case "final_response": {
                // data is JSON-encoded text — parse to recover exact spacing/newlines
                let piece = data
                try { piece = JSON.parse(data) } catch { /* fallback to raw */ }
                finalText += piece
                return { ...ex, finalTokens: [...ex.finalTokens, piece] }
              }
              case "done": {
                const p = JSON.parse(data)
                const fullResponse = finalText
                const convData = {
                  session_id: p.session_id, user_id: user?.id ?? null,
                  query: q, final_response: fullResponse,
                  agent_a_response: p.agent_a_response,
                  agent_b_response: p.agent_b_response,
                  reflection_reasoning: p.reflection_reasoning,
                  chunks_used: p.chunks_used, rating: null,
                  language: p.seeker_profile?.language,
                  seeker_level: p.seeker_profile?.level,
                }
                fetch("/api/conversation/save", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ ...convData, seeker_profile: p.seeker_profile }),
                })
                navigate(`/darshana/${p.session_id}`, { replace: false })
                // Update history for next turn
                setHistory(prev => [
                  ...prev,
                  { role: "user",      content: q },
                  { role: "assistant", content: fullResponse },
                ])
                return {
                  ...ex, done: true, conversationData: convData,
                  events: { ...ex.events, reflection_winner: p.reflection_winner },
                }
              }
              default: return ex
            }
          }))
        }
      }
    } catch {
      setExchanges(prev => prev.map(ex =>
        ex.id === id ? { ...ex, done: true, error: "Connection error. Please try again." } : ex
      ))
    } finally {
      setStreaming(false)
    }
  }, [input, streaming, user, exchanges, history])

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit() }
  }

  return (
    <>
      {showSignIn && !user && (
        <SignInModal onClose={() => setShowSignIn(false)} />
      )}

      <div style={{
        display: "flex", flexDirection: "column",
        height: "calc(100vh - 54px)", background: "var(--bg)",
      }}>
        <div ref={feedRef} style={{ flex: 1, overflowY: "auto", padding: "0 24px" }}>
          <div style={{ maxWidth: 680, margin: "0 auto", paddingTop: 32, paddingBottom: 24 }}>

            {exchanges.length === 0 && !streaming && (
              <div style={{
                display: "flex", flexDirection: "column",
                alignItems: "center", justifyContent: "center",
                height: "calc(100vh - 240px)",
                textAlign: "center", gap: 14, opacity: 0.45, userSelect: "none",
              }}>
                <p style={{
                  fontFamily: "'Noto Sans Devanagari', sans-serif",
                  fontSize: 48, color: "var(--text)", lineHeight: 1.3,
                  letterSpacing: "0.02em",
                }}>
                  तत्त्वमसि
                </p>
                <p style={{ fontSize: 15, color: "var(--muted)", fontStyle: "italic", letterSpacing: "0.04em" }}>
                  Begin your inquiry below
                </p>
              </div>
            )}

            {exchanges.map(ex => <Exchange key={ex.id} ex={ex} />)}
          </div>
        </div>

        {/* Input */}
        <div style={{
          borderTop: "1px solid var(--border)", background: "var(--bg2)",
          padding: "14px 24px 20px",
        }}>
          <form
            onSubmit={e => { e.preventDefault(); submit() }}
            style={{ maxWidth: 680, margin: "0 auto", display: "flex", gap: 10, alignItems: "flex-end" }}
          >
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInput}
              onKeyDown={onKeyDown}
              rows={1}
              placeholder={PLACEHOLDERS[phIdx]}
              disabled={streaming}
              style={{
                flex: 1, background: "var(--surface)",
                border: "1px solid var(--border2)",
                borderRadius: 10, padding: "13px 18px",
                fontSize: 17, fontFamily: "'Crimson Pro', Georgia, serif",
                color: "var(--text)", resize: "none", outline: "none",
                lineHeight: 1.6, minHeight: 52, maxHeight: 180, overflowY: "auto",
                boxShadow: "0 1px 4px rgba(0,0,0,.06)",
                transition: "border-color .2s, box-shadow .2s",
                opacity: streaming ? 0.65 : 1,
              }}
              onFocus={e => {
                e.target.style.borderColor = "var(--saffron)"
                e.target.style.boxShadow = "0 0 0 3px rgba(200,98,10,.08)"
              }}
              onBlur={e => {
                e.target.style.borderColor = "var(--border2)"
                e.target.style.boxShadow = "0 1px 3px rgba(0,0,0,.06)"
              }}
            />
            <button
              type="submit"
              disabled={streaming || !input.trim()}
              style={{
                background: "var(--saffron)", border: "none", borderRadius: 9,
                padding: "13px 22px", fontSize: 16, fontWeight: 600,
                fontFamily: "'Crimson Pro', Georgia, serif",
                color: "#fff", flexShrink: 0, letterSpacing: "0.01em", minWidth: 70,
                cursor: (streaming || !input.trim()) ? "default" : "pointer",
                opacity: (streaming || !input.trim()) ? 0.4 : 1,
                transition: "opacity .15s, background .15s",
              }}
              onMouseEnter={e => { if (!streaming && input.trim()) e.currentTarget.style.background = "var(--saffron2)" }}
              onMouseLeave={e => { e.currentTarget.style.background = "var(--saffron)" }}
            >
              {streaming ? "…" : (ASK_LABEL[lang] || "Ask")}
            </button>
          </form>
        </div>

        <Footer />
      </div>
    </>
  )
}
