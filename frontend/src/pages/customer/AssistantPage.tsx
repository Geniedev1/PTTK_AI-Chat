import { useMutation } from "@tanstack/react-query"
import { useState } from "react"
import type { FormEvent } from "react"
import type { AiChatSource } from "../../shared/types/api"
import { aiApi } from "../../shared/api/services"
import { useSessionStore } from "../../shared/stores/sessionStore"
import { getApiErrorMessage } from "../../shared/utils/apiError"

type ChatMessage = {
  role: "user" | "assistant"
  text: string
  sources?: AiChatSource[]
  retrievalMode?: string
}

export function AssistantPage() {
  const customerId = useSessionStore((state) => state.customerId)
  const cartSessionKey = useSessionStore((state) => state.cartSessionKey)
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<ChatMessage[]>([])

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
    onSuccess: (data, userMessage) => {
      setMessages((prev) => [
        ...prev,
        { role: "user", text: userMessage },
        {
          role: "assistant",
          text: data.answer,
          sources: data.sources,
          retrievalMode: data.retrieval_mode,
        },
      ])
      setInput("")
    },
  })

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || chatMutation.isPending) {
      return
    }
    chatMutation.mutate(trimmed)
  }

  return (
    <section className="panel assistant-page">
      <h1>AI Assistant</h1>
      <p>
        Chat is now connected to <strong>/api/ai/chat</strong> via gateway. Messages use current customer/session
        scope when available.
      </p>

      <div className="assistant-messages">
        {messages.length === 0 ? <p className="chat-empty">Start by asking a question about products or orders.</p> : null}

        {messages.map((message, index) => (
          <article
            className={message.role === "assistant" ? "assistant-bubble assistant" : "assistant-bubble user"}
            key={`${message.role}-${index}`}
          >
            <strong>{message.role === "assistant" ? "Assistant" : "You"}</strong>
            <p>{message.text}</p>
            {message.retrievalMode ? <small>Mode: {message.retrievalMode}</small> : null}
            {message.sources && message.sources.length > 0 ? (
              <ul className="assistant-sources">
                {message.sources.map((source, sourceIndex) => (
                  <li key={`${source.source_id}-${sourceIndex}`}>
                    <span>{source.title}</span>
                    <small>{source.source_type}</small>
                  </li>
                ))}
              </ul>
            ) : null}
          </article>
        ))}
      </div>

      <form className="assistant-form" onSubmit={submit}>
        <input
          className="field"
          placeholder="Ask about products, cart, or order status"
          value={input}
          onChange={(event) => setInput(event.target.value)}
        />
        <button className="primary-button" type="submit" disabled={chatMutation.isPending}>
          {chatMutation.isPending ? "Sending..." : "Send"}
        </button>
      </form>

      {chatMutation.isError ? <p className="error-text">{getApiErrorMessage(chatMutation.error)}</p> : null}
    </section>
  )
}
