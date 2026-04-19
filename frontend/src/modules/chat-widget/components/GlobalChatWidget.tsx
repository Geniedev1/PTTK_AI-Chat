import { useMutation } from "@tanstack/react-query"
import { useState } from "react"
import { aiApi } from "../../../shared/api/services"
import { useSessionStore } from "../../../shared/stores/sessionStore"
import { getApiErrorMessage } from "../../../shared/utils/apiError"

type WidgetMessage = {
  role: "user" | "assistant"
  text: string
}

export function GlobalChatWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<WidgetMessage[]>([])
  const [input, setInput] = useState("")
  const customerId = useSessionStore((state) => state.customerId)
  const cartSessionKey = useSessionStore((state) => state.cartSessionKey)

  const chatMutation = useMutation({
    mutationFn: (message: string) => {
      const payload: {
        message: string
        user_id?: number
        session_id?: string
        customer_id?: number
      } = { message }

      if (customerId) {
        payload.user_id = customerId
        payload.customer_id = customerId
      }
      if (cartSessionKey) {
        payload.session_id = cartSessionKey
      }

      return aiApi.chat(payload)
    },
    onSuccess: (data) => {
      setMessages((prev) => [...prev, { role: "assistant", text: data.answer }])
    },
    onError: (error) => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Request failed: ${getApiErrorMessage(error)}` },
      ])
    },
  })

  const sendMessage = () => {
    const trimmed = input.trim()
    if (!trimmed || chatMutation.isPending) {
      return
    }
    setMessages((prev) => [...prev, { role: "user", text: trimmed }])
    setInput("")
    chatMutation.mutate(trimmed)
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
              <p className={`chat-message ${message.role}`} key={`${message.role}-${index}-${message.text.slice(0, 16)}`}>
                <strong>{message.role === "assistant" ? "Assistant" : "You"}: </strong>
                {message.text}
              </p>
            ))}
            {chatMutation.isPending ? <p className="chat-empty">Assistant is thinking...</p> : null}
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
            <button onClick={sendMessage} disabled={chatMutation.isPending}>Send</button>
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
