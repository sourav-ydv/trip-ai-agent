import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'

const API_BASE = 'http://localhost:8000'

const threadId = crypto.randomUUID()

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [pendingAction, setPendingAction] = useState(null)

  function handleResult(data) {
    if (data.status === 'confirmation_required') {
      setPendingAction(data.pending_action)
    } else if (data.status === 'error') {
      setMessages((prev) => [...prev, { role: 'assistant', content: `${data.message}` }])
    } else {
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }])
    }
  }

  async function sendMessage() {
    const text = input.trim()
    if (!text || loading || pendingAction) return

    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, thread_id: threadId }),
      })
      const data = await res.json()
      handleResult(data)
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error reaching backend: ${err.message}` },
      ])
    } finally {
      setLoading(false)
    }
  }

  async function confirmAction(approved) {
    setLoading(true)
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: approved ? 'Approved' : 'Declined' },
    ])
    setPendingAction(null)

    try {
      const res = await fetch(`${API_BASE}/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id: threadId, approved }),
      })
      const data = await res.json()
      handleResult(data)
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error reaching backend: ${err.message}` },
      ])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="app">
      <h1>Trip AI Agent</h1>
      <div className="chat-window">
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            {m.role === 'assistant' ? (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  table: ({ node, ...props }) => (
                    <div className="table-wrapper">
                      <table {...props} />
                    </div>
                  ),
                }}
              >
                {m.content}
              </ReactMarkdown>
            ) : (
              m.content
            )}
          </div>
        ))}
        {loading && <div className="bubble assistant loading">thinking…</div>}

        {pendingAction && (
          <div className="confirm-card">
            <div className="confirm-title">Confirmation needed</div>
            <div className="confirm-details">{pendingAction.details}</div>
            <div className="confirm-buttons">
              <button className="approve" onClick={() => confirmAction(true)} disabled={loading}>
                Approve
              </button>
              <button className="decline" onClick={() => confirmAction(false)} disabled={loading}>
                Decline
              </button>
            </div>
          </div>
        )}
      </div>
      <div className="input-row">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={pendingAction ? 'Respond to the confirmation above first…' : 'Plan a trip...'}
          rows={2}
          disabled={!!pendingAction}
        />
        <button onClick={sendMessage} disabled={loading || !!pendingAction}>
          Send
        </button>
      </div>
    </div>
  )
}