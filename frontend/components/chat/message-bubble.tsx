"use client"

import { User } from "lucide-react"

import { cn } from "@/lib/utils"

import type { Message } from "./chat-shell"
import { AssistantAvatar } from "./assistant-avatar"
import { MarkdownRenderer } from "./markdown-renderer"

interface MessageBubbleProps {
  message: Message
  isStreaming?: boolean
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
}

export function MessageBubble({ message, isStreaming = false }: MessageBubbleProps) {
  const isUser = message.role === "user"

  return (
    <div
      className={cn(
        "flex max-w-[90%] gap-2 md:max-w-[80%]",
        isUser
          ? "user-message-enter ml-auto flex-row-reverse"
          : "animate-in slide-in-from-bottom-2 fade-in mr-auto items-end duration-300",
      )}
    >
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-white ring-1 ring-stone-200 dark:bg-stone-800 dark:ring-stone-700" : "bg-transparent",
          !isUser && isStreaming && "sticky bottom-4 self-end transition-all duration-300",
        )}
        aria-hidden="true"
      >
        {isUser ? (
          <User className="h-4 w-4 text-stone-800 dark:text-stone-200" />
        ) : (
          <AssistantAvatar className="h-8 w-8 shrink-0" />
        )}
      </div>

      <div className={cn("flex flex-col", isUser ? "items-end" : "items-start")}>
        <span className="mt-2 mb-1 hidden text-xs text-stone-400 dark:text-stone-500 sm:block">
          {isUser ? "You" : "Assistant"}
        </span>

        <div
          className={cn(
            "overflow-hidden rounded-2xl",
            isUser
              ? "rounded-br-md border border-stone-200 bg-white text-stone-800 shadow-sm dark:border-stone-700 dark:bg-stone-900 dark:text-stone-100"
              : "rounded-bl-md bg-transparent text-stone-800 dark:text-stone-100",
          )}
          style={{
            willChange: isStreaming ? "height" : "auto",
            transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
          }}
        >
          <div
            className={cn(isUser ? "px-4 py-3" : "py-1")}
            style={{
              transition: "max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease",
            }}
          >
            {isUser ? (
              <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
            ) : (
              <div className="flex flex-col gap-3">
                <MarkdownRenderer content={message.content || " "} isStreaming={isStreaming} />
                {!!message.citations?.length && (
                  <div className="px-4 pb-3">
                    <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.18em] text-stone-400 dark:text-stone-500">
                      Sources
                    </p>
                    <ul className="space-y-1.5">
                      {message.citations.map((citation, index) => (
                        <li
                          key={`${citation.url || citation.document_name}-${index}`}
                          className="text-xs text-stone-500 dark:text-stone-400"
                        >
                          {citation.url ? (
                            <a
                              href={citation.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-emerald-700 underline decoration-emerald-200 underline-offset-2 hover:text-emerald-800 dark:text-emerald-400 dark:decoration-emerald-900 dark:hover:text-emerald-300"
                            >
                              {citation.title}
                            </a>
                          ) : (
                            citation.document_name
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <span className="mt-1 text-xs text-stone-400 dark:text-stone-500">{formatTime(message.createdAt)}</span>
      </div>
    </div>
  )
}
