import { useState, useRef, useEffect, useCallback } from "react"
import { useParams, useLocation } from "react-router-dom"
import ThinkingPanel from "../components/ThinkingPanel"
import FinalResponse from "../components/FinalResponse"
import Feedback from "../components/Feedback"
import Footer from "../components/Footer"
import { signInWithGoogle } from "../lib/supabase"
// NOTE: the base64 fallback (assets-shankara.js, ~1MB) is imported LAZILY inside
// ShankaraBackdrop only when the static /shankara-bg.jpg is unavailable, so it
// never bloats the main bundle.

const PLACEHOLDERS = [
  "Ask what you have always wondered…",
  "अथातो ब्रह्म जिज्ञासा — now, therefore, the inquiry into Brahman…",
  "What is the Self? What is real?",
  "Bring your question to Śaṅkara's presence…",
]

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
        <p className="deva" style={{
          fontSize: 26, color: "var(--saffron)",
          marginBottom: 10, fontStyle: "normal", lineHeight: 1.5,
        }}>अथातो ब्रह्म जिज्ञासा</p>
        <p style={{ fontSize: 19, color: "var(--text)", marginBottom: 8, fontWeight: 600 }}>
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

// ─── Opening ──────────────────────────────────────────────────────────────────
// The threshold. The praṇām-śloka to Śaṅkara as the typographic centerpiece,
// a faint yantra breathing behind it, and real questions a seeker may ask —
// each a single tap away.
const STOTRA = [
  "श्रुतिस्मृतिपुराणानाम् आलयं करुणालयम् ।",
  "नमामि भगवत्पादं शङ्करं लोकशङ्करम् ॥",
]

const SEED_QUESTIONS = [
  "ब्रह्म किम्? — What is Brahman?",
  "Who am I, truly?",
  "What is māyā, and why does the world appear?",
  "How do I begin a spiritual journey?",
  "What does “Tat tvam asi” mean?",
  "How can I be free from suffering?",
]

// A faint Śaṅkara presence behind the page — Raja Ravi Varma's public-domain
// painting, anchored to the far right and dissolved into the paper on every
// edge so it reads as a watermark in the margin, never a hard-edged photo that
// collides with the text.
//
// Source strategy: prefer the crisp static file (/shankara-bg.jpg, generated at
// Docker build time → served standalone, browser-cached, no JS bloat). If that
// file is somehow unavailable, fall back to the inlined base64 (shankaraBg) so
// the watermark never simply vanishes.
const STATIC_BG = "/shankara-bg.jpg"

function ShankaraBackdrop() {
  // Two stacked masks: a left→right fade (so it never reaches the text column)
  // and a vertical fade (so the top/bottom edges melt into the page).
  const mask =
    "linear-gradient(to left, #000 0%, #000 28%, transparent 82%), " +
    "linear-gradient(to bottom, transparent 0%, #000 22%, #000 72%, transparent 100%)"

  // Start on the static file; if it 404s, lazily pull in the base64 fallback
  // (dynamic import keeps that ~1MB out of the main bundle).
  const [src, setSrc] = useState(STATIC_BG)
  useEffect(() => {
    const probe = new Image()
    probe.onerror = () => {
      import("../assets-shankara.js").then(m => setSrc(m.default)).catch(() => {})
    }
    probe.src = STATIC_BG
  }, [])

  return (
    <div
      aria-hidden
      className="shankara-backdrop"
      style={{
        position: "fixed", top: 0, right: 0, bottom: 0,
        width: "min(46vw, 600px)", zIndex: 0, pointerEvents: "none",
        backgroundImage: `url(${src})`,
        backgroundSize: "cover",
        backgroundPosition: "right 30%",
        backgroundRepeat: "no-repeat",
        opacity: 0.1,
        filter: "sepia(0.5) contrast(0.92) brightness(1.04)",
        WebkitMaskImage: mask, maskImage: mask,
        WebkitMaskComposite: "source-in", maskComposite: "intersect",
        animation: "drift 2.4s var(--ease-ink) both",
      }}
    />
  )
}

// Typewriter: inscribe text character by character. Returns the visible slice
// and whether it's done, so a cursor can blink at the writing point.
function useTypewriter(fullText, speed = 55, startDelay = 350) {
  const [n, setN] = useState(0)
  useEffect(() => {
    let i = 0, timer
    const begin = setTimeout(function tick() {
      i += 1
      setN(i)
      if (i < fullText.length) timer = setTimeout(tick, speed)
    }, startDelay)
    return () => { clearTimeout(begin); clearTimeout(timer) }
  }, [fullText, speed, startDelay])
  return { shown: fullText.slice(0, n), done: n >= fullText.length }
}

function Opening({ onAsk }) {
  // Inscribe the whole stotra (both lines) as one continuous hand.
  const full = STOTRA.join("\n")
  const { shown, done } = useTypewriter(full, 52, 500)
  const lines = shown.split("\n")

  return (
    <div style={{
      position: "relative",
      display: "flex", flexDirection: "column", justifyContent: "center",
      paddingTop: "var(--space-lg)", paddingBottom: "var(--space-md)",
    }}>
      <ShankaraBackdrop />

      <div style={{ position: "relative", zIndex: 1 }}>
        {/* a small breathing flame */}
        <span style={{
          width: 11, height: 18,
          borderRadius: "50% 50% 50% 50% / 64% 64% 36% 36%",
          background: "linear-gradient(180deg,#D2611C 0%,#B23A1E 72%)",
          display: "block", flexShrink: 0, marginBottom: "var(--space-lg)",
          boxShadow: "0 0 26px rgba(178,58,30,.34)",
          animation: "flamebreath 3.4s ease-in-out infinite",
        }} />

        {/* The stotra — inscribed character by character, manuscript hand. */}
        <div style={{ marginBottom: "var(--space-lg)", userSelect: "none", minHeight: "4.4em" }}>
          {lines.map((line, i) => (
            <p key={i} className="deva" style={{
              fontSize: "clamp(1.5rem, 3.8vw, 2.5rem)",
              color: "var(--ink)", lineHeight: 1.55,
              letterSpacing: ".004em",
            }}>
              {line}
              {/* writing cursor on the last visible line until done */}
              {!done && i === lines.length - 1 && (
                <span style={{
                  display: "inline-block", width: 2, height: "1em",
                  background: "var(--flame)", verticalAlign: "text-bottom",
                  marginLeft: 2, animation: "flamebreath 1s ease-in-out infinite",
                }} />
              )}
            </p>
          ))}
          <p className="display" style={{
            marginTop: "var(--space-sm)", fontStyle: "italic",
            fontSize: "1.06rem", color: "var(--ink-faint)", maxWidth: 540,
            lineHeight: 1.6,
            opacity: done ? 1 : 0,
            transition: "opacity .8s var(--ease-ink)",
          }}>
            Abode of śruti, smṛti and purāṇa, abode of compassion — I bow to
            Bhagavatpāda Śaṅkara, who brings well-being to the world.
          </p>
        </div>

        {/* Real questions — each a tap away. */}
        <div style={{ animation: "drift 1.7s var(--ease-ink) both" }}>
          <div className="mono" style={{
            fontSize: ".66rem", letterSpacing: ".14em", textTransform: "uppercase",
            color: "var(--ink-faint)", marginBottom: "var(--space-sm)",
          }}>
            you might ask
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10, maxWidth: 640 }}>
            {SEED_QUESTIONS.map((q, i) => {
              const text = q.includes("—") ? q.split("—")[1].trim() : q
              return (
                <button
                  key={i}
                  onClick={() => onAsk(q.includes("—") ? q.split("—")[0].trim() + " " + text : q)}
                  className="seed-chip"
                  style={{
                    border: "1px solid var(--rule-2)",
                    background: "var(--vellum)",
                    color: "var(--ink-soft)",
                    borderRadius: 999,
                    padding: "9px 16px",
                    fontSize: ".92rem", fontFamily: "var(--font-body)",
                    cursor: "pointer", lineHeight: 1.3,
                    transition: "all .2s var(--ease-ink)",
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.borderColor = "var(--flame)"
                    e.currentTarget.style.color = "var(--flame-2)"
                    e.currentTarget.style.background = "var(--paper-3)"
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.borderColor = "var(--rule-2)"
                    e.currentTarget.style.color = "var(--ink-soft)"
                    e.currentTarget.style.background = "var(--vellum)"
                  }}
                >
                  {q.includes("—")
                    ? <><span className="deva" style={{ fontSize: "1.05em" }}>{q.split("—")[0].trim()}</span> <span style={{ color: "var(--ink-faint)" }}>· {text}</span></>
                    : q}
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Exchange ─────────────────────────────────────────────────────────────────
function Exchange({ ex }) {
  return (
    <article style={{ marginBottom: "var(--space-2xl)" }}>
      {/* The seeker's question — an inscription, not a chat bubble.
          Marginal label + the question in display serif, left-aligned,
          underlined by a hairline that draws itself in. */}
      <div style={{ marginBottom: "var(--space-lg)" }}>
        <div className="mono" style={{
          fontSize: ".68rem", letterSpacing: ".14em", textTransform: "uppercase",
          color: "var(--ink-faint)", marginBottom: "var(--space-2xs)",
        }}>
          the seeker asks
        </div>
        <p className="display" style={{
          fontSize: "1.46rem", lineHeight: 1.4, color: "var(--ink)",
          fontWeight: 400, letterSpacing: "-.005em",
        }}>
          {ex.question}
        </p>
        <div style={{
          height: 2, marginTop: "var(--space-sm)", width: "100%",
          background: "linear-gradient(90deg, var(--flame) 0%, var(--flame) 36px, var(--rule) 36px, var(--rule) 100%)",
          transformOrigin: "left",
          animation: "hairline .7s var(--ease-ink) both",
        }} />
      </div>

      {ex.rateLimited ? (
        <div style={{
          background: "var(--vellum)", border: "1px solid var(--rule-2)",
          borderRadius: 4, padding: "var(--space-md) var(--space-lg)",
          borderLeft: "3px solid var(--flame)",
        }}>
          <p style={{ fontSize: 16.5, color: "var(--ink-soft)", lineHeight: 1.75, marginBottom: 12 }}>
            {ex.rateLimited.message}
          </p>
          {ex.rateLimited.reset_at && (
            <p className="mono" style={{ fontSize: 12, color: "var(--muted)", marginBottom: 8 }}>
              resets at {new Date(ex.rateLimited.reset_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </p>
          )}
          <a href="https://github.com/SujayKulkarni-2211/SankaRAGamana"
            target="_blank" rel="noreferrer"
            style={{ fontSize: 13, color: "var(--flame)", textDecoration: "none" }}>
            view source on GitHub →
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
  const location = useLocation()
  const isDarshanaRoute = location.pathname.startsWith("/darshana/")
  const [input,       setInput]       = useState("")
  const [exchanges,   setExchanges]   = useState([])
  const [streaming,   setStreaming]   = useState(false)
  const [phIdx,       setPhIdx]       = useState(0)
  const [focused,     setFocused]     = useState(false)
  // true when the page is scrolled to (or near) the bottom — used to dissolve
  // the input band so the painting shows through near the footer.
  const [atBottom,    setAtBottom]    = useState(false)
  // Show modal on entry for anonymous users
  const [showSignIn, setShowSignIn] = useState(!user)
  useEffect(() => { if (user) setShowSignIn(false) }, [user])
  // history = [{role, content}] pairs sent to backend for context
  const [history,     setHistory]     = useState([])
  const textareaRef = useRef()
  const feedRef     = useRef()
  // session_id we just created in this tab — the load effect skips re-fetching
  // it (the streamed answer is already in memory).
  const justCreatedRef = useRef(null)
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
    // We just created this session in-tab — the answer is already on screen.
    // Skip the re-fetch (it can race the save and blank the view).
    if (justCreatedRef.current === session_id) {
      justCreatedRef.current = null
      return
    }
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

  // Auto-scroll — the scroll container is now an ancestor, so walk up to the
  // nearest scrollable element and pin it to the bottom.
  useEffect(() => {
    let el = feedRef.current?.parentElement
    while (el && el.scrollHeight <= el.clientHeight) el = el.parentElement
    if (el) el.scrollTop = el.scrollHeight
  }, [exchanges])

  // Watch the scroll container so the input band can dissolve near the footer.
  useEffect(() => {
    let el = feedRef.current?.parentElement
    while (el && getComputedStyle(el).overflowY !== "auto" && el !== document.body) {
      el = el.parentElement
    }
    if (!el) return
    const onScroll = () => {
      const remaining = el.scrollHeight - el.scrollTop - el.clientHeight
      setAtBottom(remaining < 120)  // within 120px of the bottom (footer area)
    }
    onScroll()
    el.addEventListener("scroll", onScroll, { passive: true })
    return () => el.removeEventListener("scroll", onScroll)
  }, [exchanges])

  function handleInput(e) {
    setInput(e.target.value)
    e.target.style.height = "auto"
    e.target.style.height = Math.min(e.target.scrollHeight, 180) + "px"
  }

  const submit = useCallback(async (explicit) => {
    const q = (typeof explicit === "string" ? explicit : input).trim()
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
      let doneConvData = null
      let doneWinner = null

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

          // ── Side effects FIRST, outside the state updater ──────────────
          // React StrictMode runs setState updaters twice in dev; any closure
          // mutation inside them (e.g. finalText += piece) would double. So we
          // accumulate text and fire save/navigate here, exactly once.
          if (event === "final_response") {
            let piece = data
            try { piece = JSON.parse(data) } catch { /* raw */ }
            finalText += piece
          }
          if (event === "done") {
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
            // Update ONLY the URL bar (so the darshana is shareable/bookmarkable)
            // without triggering a React Router route swap — that would remount
            // Chat and wipe the just-streamed answer from memory, then race the
            // save with a re-fetch. history.replaceState changes the path quietly.
            window.history.replaceState(null, "", `/darshana/${p.session_id}`)
            setHistory(prev => [
              ...prev,
              { role: "user",      content: q },
              { role: "assistant", content: fullResponse },
            ])
            doneConvData = convData
            doneWinner = p.reflection_winner
          }

          setExchanges(prev => prev.map(ex => {
            if (ex.id !== id) return ex
            switch (event) {
              case "rate_limited":
                return { ...ex, rateLimited: JSON.parse(data), done: true }
              case "profile":
                return { ...ex, events: { ...ex.events, profile: JSON.parse(data) } }
              case "agent_a_translation": {
                let v = data
                try { v = JSON.parse(data) } catch { /* fallback */ }
                return { ...ex, events: { ...ex.events, agent_a_translation: v } }
              }
              case "agent_a_chunks":
                return { ...ex, events: { ...ex.events, agent_a_chunks: JSON.parse(data) } }
              case "agent_a_response": {
                let t = data
                try { t = JSON.parse(data) } catch { /* fallback */ }
                return { ...ex, events: { ...ex.events, agent_a_response_tokens: [...(ex.events.agent_a_response_tokens||[]), t] } }
              }
              case "agent_b_chunks":
                return { ...ex, events: { ...ex.events, agent_b_chunks: JSON.parse(data) } }
              case "agent_b_response": {
                let t = data
                try { t = JSON.parse(data) } catch { /* fallback */ }
                return { ...ex, events: { ...ex.events, agent_b_response_tokens: [...(ex.events.agent_b_response_tokens||[]), t] } }
              }
              case "reflection_reasoning": {
                let r = data
                try { r = JSON.parse(data) } catch { /* fallback */ }
                return { ...ex, events: { ...ex.events, reflection_reasoning_tokens: [r] } }
              }
              case "final_response": {
                // PURE: parse and append to the token array only. The closure
                // accumulator finalText is handled above (once, outside updater).
                let piece = data
                try { piece = JSON.parse(data) } catch { /* fallback to raw */ }
                return { ...ex, finalTokens: [...ex.finalTokens, piece] }
              }
              case "done": {
                // PURE: side effects (save/navigate/history) ran above. Here we
                // only mark the exchange done using values captured outside.
                return {
                  ...ex, done: true, conversationData: doneConvData,
                  events: { ...ex.events, reflection_winner: doneWinner },
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

  // A seed-question chip: show it in the input, then ask.
  function askSeed(q) {
    setInput(q)
    submit(q)
  }

  return (
    <>
      {showSignIn && !user && (
        <SignInModal onClose={() => setShowSignIn(false)} />
      )}

      <div style={{
        display: "flex", flexDirection: "column",
        minHeight: "100%", background: "var(--bg)",
      }}>
        <div ref={feedRef} style={{ flex: 1, padding: "0 var(--space-md)" }}>
          <div style={{ maxWidth: "var(--measure)", margin: "0 auto", paddingTop: "var(--space-xl)", paddingBottom: "var(--space-lg)" }}>

            {exchanges.length === 0 && !streaming && (
              <Opening onAsk={askSeed} />
            )}

            {exchanges.map(ex => <Exchange key={ex.id} ex={ex} />)}
          </div>
        </div>

        {/* Input — a single writing surface, pinned to the bottom of the view.
            The band is solid while reading/typing, but dissolves to transparent
            once scrolled to the footer so the painting shows through there. */}
        <div style={{
          position: "sticky", bottom: 0, zIndex: 5,
          borderTop: atBottom ? "1px solid transparent" : "1px solid var(--rule)",
          background: atBottom ? "transparent" : "var(--paper-2)",
          padding: "var(--space-md) var(--space-md) var(--space-lg)",
          transition: "background .35s var(--ease-ink), border-color .35s",
        }}>
          <form
            onSubmit={e => { e.preventDefault(); submit() }}
            style={{
              maxWidth: "var(--measure)", margin: "0 auto",
              display: "flex", gap: 0, alignItems: "stretch",
              background: "var(--vellum)",
              border: "1px solid var(--rule-2)",
              borderRadius: 14,
              boxShadow: focused ? "0 0 0 3px rgba(200,67,28,.08), 0 4px 18px rgba(32,36,46,.06)"
                                  : "0 1px 4px rgba(32,36,46,.05)",
              transition: "box-shadow .25s var(--ease-ink), border-color .25s",
              borderColor: focused ? "var(--flame)" : "var(--rule-2)",
              overflow: "hidden",
            }}
          >
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInput}
              onKeyDown={onKeyDown}
              rows={1}
              placeholder={PLACEHOLDERS[phIdx]}
              disabled={streaming}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              style={{
                flex: 1, background: "transparent", border: "none",
                padding: "15px 20px", fontSize: 17, fontFamily: "var(--font-body)",
                color: "var(--ink)", resize: "none", outline: "none",
                lineHeight: 1.6, minHeight: 54, maxHeight: 180, overflowY: "auto",
                opacity: streaming ? 0.6 : 1,
              }}
            />
            <button
              type="submit"
              disabled={streaming || !input.trim()}
              aria-label="Ask"
              style={{
                background: (streaming || !input.trim()) ? "transparent" : "var(--flame)",
                border: "none", borderLeft: "1px solid var(--rule-2)",
                padding: "0 22px", fontSize: 15, fontWeight: 500,
                fontFamily: "var(--font-mono)", letterSpacing: ".06em",
                textTransform: "lowercase",
                color: (streaming || !input.trim()) ? "var(--ink-faint)" : "var(--vellum)",
                flexShrink: 0, cursor: (streaming || !input.trim()) ? "default" : "pointer",
                transition: "background .2s, color .2s",
                display: "flex", alignItems: "center", gap: 8,
              }}
              onMouseEnter={e => { if (!streaming && input.trim()) e.currentTarget.style.background = "var(--flame-2)" }}
              onMouseLeave={e => { if (!streaming && input.trim()) e.currentTarget.style.background = "var(--flame)" }}
            >
              {streaming
                ? <span style={{
                    width: 8, height: 10, borderRadius: "50% 50% 50% 50% / 62% 62% 38% 38%",
                    background: "var(--flame)", animation: "flamebreath 1.4s ease-in-out infinite",
                  }} />
                : (ASK_LABEL[lang] || "ask")}
            </button>
          </form>
          <p className="mono" style={{
            maxWidth: "var(--measure)", margin: "var(--space-xs) auto 0",
            fontSize: ".64rem", letterSpacing: ".06em", color: "var(--ink-faint)",
            opacity: .7, textAlign: "right", paddingRight: 4,
          }}>
            ↵ to ask · ⇧↵ for a new line
          </p>
        </div>

        <Footer />
      </div>
    </>
  )
}
