import { useState } from "react"

export default function Feedback({ conversationData }) {
  const [rating, setRating] = useState(null) // true | false
  const [text, setText] = useState("")
  const [submitted, setSubmitted] = useState(false)
  const [expanded, setExpanded] = useState(false)

  async function submit() {
    await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...conversationData,
        rating,
        feedback_text: text || null,
      }),
    })
    setSubmitted(true)
  }

  if (submitted) {
    return (
      <p className="text-xs text-[var(--muted)] mt-3">
        Noted.{" "}
        <span className="font-['Noto_Sans_Devanagari'] text-[var(--saffron)]">शुभम्।</span>
      </p>
    )
  }

  return (
    <div className="mt-4 pt-3 border-t border-[var(--border)]">
      <div className="flex items-center gap-3">
        <button
          onClick={() => { setRating(true); setExpanded(true) }}
          className={`text-lg transition-opacity ${rating === true ? "opacity-100" : "opacity-40 hover:opacity-70"}`}
        >👍</button>
        <button
          onClick={() => { setRating(false); setExpanded(true) }}
          className={`text-lg transition-opacity ${rating === false ? "opacity-100" : "opacity-40 hover:opacity-70"}`}
        >👎</button>

        {rating !== null && !expanded && (
          <button
            onClick={submit}
            className="text-xs text-[var(--saffron)] hover:underline ml-2"
          >Submit</button>
        )}
      </div>

      {expanded && (
        <div className="mt-2 space-y-2">
          <textarea
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder="What felt right or wrong about this response? (optional)"
            rows={2}
            className="w-full bg-[#161412] border border-[var(--border)] rounded px-3 py-2 text-sm text-[var(--text)] placeholder-[var(--muted)] resize-none focus:outline-none focus:border-[var(--saffron)]"
          />
          <div className="flex items-center justify-between">
            <p className="text-[10px] text-[var(--muted)] max-w-sm leading-relaxed">
              We periodically review feedback to improve how Śaṅkarācārya's teachings
              are represented here. This takes time and care.
            </p>
            <button
              onClick={submit}
              disabled={rating === null}
              className="text-xs px-3 py-1 rounded bg-[var(--saffron)] text-[var(--bg)] font-semibold hover:opacity-90 disabled:opacity-40 transition-opacity"
            >Submit</button>
          </div>
        </div>
      )}
    </div>
  )
}
