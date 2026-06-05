import { useEffect, useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import Footer from "../components/Footer"

export default function History({ user }) {
  const navigate = useNavigate()
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) { navigate("/"); return }
    fetch(`/api/conversations/history?user_id=${user.id}`)
      .then(r => r.json())
      .then(d => { setHistory(d || []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [user, navigate])

  if (!user) return null

  return (
    <div className="flex flex-col min-h-[calc(100vh-52px)]">
      <main className="flex-1 max-w-2xl w-full mx-auto px-4 py-8">
        <h2 className="text-xl font-semibold text-[var(--text)] mb-6">My Darśanas</h2>

        {loading && (
          <p className="text-[var(--muted)] text-sm">Loading…</p>
        )}

        {!loading && history.length === 0 && (
          <p className="text-[var(--muted)] text-sm">No saved darśanas yet. Ask a question to begin.</p>
        )}

        <div className="space-y-2">
          {history.map(item => (
            <Link
              key={item.session_id}
              to={`/darshana/${item.session_id}`}
              className="block bg-[var(--card)] border border-[var(--border)] rounded-lg px-4 py-3 hover:border-[var(--saffron)] transition-colors group"
            >
              <p className="text-[var(--text)] text-sm truncate group-hover:text-[var(--saffron)] transition-colors">
                {item.query}
              </p>
              <div className="flex gap-3 mt-1 text-[10px] text-[var(--muted)]">
                <span>{new Date(item.created_at).toLocaleDateString()}</span>
                {item.language && <span>{item.language}</span>}
              </div>
            </Link>
          ))}
        </div>
      </main>
      <Footer />
    </div>
  )
}
