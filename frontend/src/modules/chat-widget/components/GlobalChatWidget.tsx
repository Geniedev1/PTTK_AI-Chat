import { useState } from "react"

export function GlobalChatWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<string[]>([])
  const [input, setInput] = useState("")

  const sendMessage = () => {
    const trimmed = input.trim()
    if (!trimmed) {
      return
    }
    setMessages((prev) => [...prev, trimmed])
    setInput("")
  }

  return (
    <div className="chat-widget-root" aria-live="polite">
      {isOpen && (
        <section className="chat-panel" aria-label="Global chat widget">
          <header className="chat-panel-header">
            <strong>Assistant</strong>
            <button onClick={() => setIsOpen(false)} aria-label="Close chat">Close</button>
          </header>
          <div className="chat-panel-body">
            {messages.length === 0 ? <p className="chat-empty">No messages yet.</p> : null}
            {messages.map((message, index) => (
              <p className="chat-message" key={`${message}-${index}`}>
                {message}
              </p>
            ))}
          </div>
          <footer className="chat-panel-footer">
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Type your message"
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  sendMessage()
                }
              }}
            />
            <button onClick={sendMessage}>Send</button>
          </footer>
        </section>
      )}
      <button
        className="chat-launcher"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label="Toggle assistant chat"
      >
        {isOpen ? "-" : "AI"}
      </button>
    </div>
  )
}
