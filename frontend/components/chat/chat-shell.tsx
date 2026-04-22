"use client"

import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from "react"
import { MessageSquareDashed, Moon, Sun } from "lucide-react"

import { Button } from "@/components/ui/button"

import { Composer } from "./composer"
import { MessageList } from "./message-list"

export interface Citation {
  title: string
  url: string
  document_name: string
}

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  createdAt: Date
  citations?: Citation[]
}

const STORAGE_KEY = "optibot-chat-messages"
const THEME_KEY = "optibot-theme"

type Theme = "light" | "dark"

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "light"

  const stored = window.localStorage.getItem(THEME_KEY)
  if (stored === "light" || stored === "dark") {
    return stored
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

function applyAssistantPatch(
  targetId: string,
  patch: Partial<Pick<Message, "content" | "citations">>,
) {
  return (previous: Message[]) =>
    previous.map((message) => (message.id === targetId ? { ...message, ...patch } : message))
}

function parseSseChunk(rawEvent: string): { event: string; data: string } | null {
  const trimmed = rawEvent.trim()
  if (!trimmed) return null

  let event = "message"
  const dataLines: string[] = []

  for (const line of trimmed.split(/\r?\n/)) {
    if (line.startsWith("event:")) {
      event = line.slice("event:".length).trim()
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trim())
    }
  }

  return { event, data: dataLines.join("\n") }
}

function consumeSseEvents(
  rawEvents: string[],
  assistantMessageId: string,
  accumulatedContentRef: { value: string },
  setMessages: Dispatch<SetStateAction<Message[]>>,
) {
  for (const rawEvent of rawEvents) {
    const parsed = parseSseChunk(rawEvent)
    if (!parsed) continue

    const payload = parsed.data ? JSON.parse(parsed.data) : {}
    if (parsed.event === "token") {
      accumulatedContentRef.value += String(payload.text || "")
      setMessages(applyAssistantPatch(assistantMessageId, { content: accumulatedContentRef.value }))
    } else if (parsed.event === "done") {
      accumulatedContentRef.value = String(payload.answer || accumulatedContentRef.value)
      setMessages(
        applyAssistantPatch(assistantMessageId, {
          content: accumulatedContentRef.value,
          citations: Array.isArray(payload.citations) ? payload.citations : [],
        }),
      )
    } else if (parsed.event === "error") {
      throw new Error(String(payload.error || "Streaming failed"))
    }
  }
}

export function ChatShell() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [abortController, setAbortController] = useState<AbortController | null>(null)
  const [isLoaded, setIsLoaded] = useState(false)
  const [theme, setTheme] = useState<Theme>(getInitialTheme)

  useEffect(() => {
    const root = document.documentElement
    root.classList.toggle("dark", theme === "dark")
    root.style.colorScheme = theme
    window.localStorage.setItem(THEME_KEY, theme)
  }, [theme])

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        setMessages(
          parsed.map((msg: Message) => ({
            ...msg,
            createdAt: new Date(msg.createdAt),
          })),
        )
      }
    } catch (e) {
      console.error("Failed to load from localStorage:", e)
    } finally {
      setIsLoaded(true)
    }
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
    } catch (e) {
      console.error("Failed to save messages to localStorage:", e)
    }
  }, [messages])

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isStreaming) return

      setError(null)

      const userMessage: Message = {
        id: generateId(),
        role: "user",
        content: content.trim(),
        createdAt: new Date(),
      }
      const assistantMessage: Message = {
        id: generateId(),
        role: "assistant",
        content: "",
        createdAt: new Date(),
      }

      setMessages((prev) => [...prev, userMessage, assistantMessage])
      setIsStreaming(true)

      const controller = new AbortController()
      setAbortController(controller)

      try {
        const response = await fetch("/api/chat/stream", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
          },
          body: JSON.stringify({
            messages: [...messages, userMessage].map((message) => ({
              role: message.role,
              content: message.content,
            })),
          }),
          signal: controller.signal,
        })

        if (!response.ok) {
          const errorPayload = await response.json().catch(() => null)
          throw new Error(errorPayload?.error || `HTTP error! status: ${response.status}`)
        }

        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error("No response body")
        }

        const decoder = new TextDecoder()
        let buffer = ""
        const accumulatedContentRef = { value: "" }

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const events = buffer.split("\n\n")
          buffer = events.pop() || ""

          consumeSseEvents(events, assistantMessage.id, accumulatedContentRef, setMessages)
        }

        if (buffer.trim()) {
          consumeSseEvents([buffer], assistantMessage.id, accumulatedContentRef, setMessages)
        }
      } catch (e) {
        if (e instanceof Error && e.name === "AbortError") {
          setMessages((prev) =>
            prev.map((message) =>
              message.id === assistantMessage.id
                ? { ...message, content: message.content || "[Cancelled]" }
                : message,
            ),
          )
        } else {
          console.error("Error sending message:", e)
          setError(e instanceof Error ? e.message : "An error occurred")
          setMessages((prev) => prev.filter((message) => message.id !== assistantMessage.id))
        }
      } finally {
        setIsStreaming(false)
        setAbortController(null)
      }
    },
    [isStreaming, messages],
  )

  const retry = useCallback(() => {
    if (messages.length === 0) return

    const lastUserMessage = [...messages].reverse().find((message) => message.role === "user")
    if (!lastUserMessage) return

    const index = messages.findIndex((message) => message.id === lastUserMessage.id)
    setMessages(messages.slice(0, index))
    setError(null)
    setTimeout(() => sendMessage(lastUserMessage.content), 100)
  }, [messages, sendMessage])

  const stopStreaming = useCallback(() => {
    abortController?.abort()
  }, [abortController])

  const clearChat = useCallback(() => {
    setMessages([])
    setError(null)
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  const toggleTheme = useCallback(() => {
    setTheme((current) => (current === "dark" ? "light" : "dark"))
  }, [])

  return (
    <div
      className="relative h-dvh overflow-hidden bg-stone-50 text-stone-950 transition-colors duration-300 dark:bg-stone-950 dark:text-stone-50"
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(16,185,129,0.08),transparent_36%)] dark:bg-[radial-gradient(circle_at_top,rgba(45,212,191,0.14),transparent_34%),radial-gradient(circle_at_bottom,rgba(59,130,246,0.12),transparent_30%)]" />

      <Button
        onClick={clearChat}
        variant="ghost"
        size="icon"
        className="absolute top-4 left-4 z-20 h-10 w-10 rounded-full border border-stone-200 bg-white/90 text-stone-700 shadow-sm backdrop-blur hover:bg-stone-100 dark:border-stone-800 dark:bg-stone-900/85 dark:text-stone-200 dark:hover:bg-stone-800"
        aria-label="Reset chat"
      >
        <MessageSquareDashed className="h-5 w-5" />
      </Button>

      <Button
        onClick={toggleTheme}
        variant="ghost"
        size="icon"
        className="absolute top-4 right-4 z-20 h-10 w-10 rounded-full border border-stone-200 bg-white/90 text-stone-700 shadow-sm backdrop-blur hover:bg-stone-100 dark:border-stone-800 dark:bg-stone-900/85 dark:text-stone-200 dark:hover:bg-stone-800"
        aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      >
        {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
      </Button>

      <MessageList
        messages={messages}
        isStreaming={isStreaming}
        error={error}
        onRetry={retry}
        isLoaded={isLoaded}
      />

      <Composer onSend={sendMessage} onStop={stopStreaming} isStreaming={isStreaming} disabled={false} />
    </div>
  )
}
