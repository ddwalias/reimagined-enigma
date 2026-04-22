"use client"

import { AssistantAvatar } from "./assistant-avatar"

export function TypingIndicator() {
  return (
    <div className="mr-auto flex max-w-[90%] gap-3 animate-in fade-in slide-in-from-bottom-2 duration-300 md:max-w-[80%]">
      <div className="shrink-0">
        <AssistantAvatar />
      </div>

      {/* Typing dots */}
      <div
        className="rounded-2xl rounded-bl-md border border-stone-200 bg-white px-4 py-3 dark:border-stone-800 dark:bg-stone-900"
        style={{
          boxShadow:
            "rgba(14, 63, 126, 0.04) 0px 0px 0px 1px, rgba(42, 51, 69, 0.04) 0px 1px 1px -0.5px, rgba(42, 51, 70, 0.04) 0px 3px 3px -1.5px, rgba(42, 51, 70, 0.04) 0px 6px 6px -3px, rgba(14, 63, 126, 0.04) 0px 12px 12px -6px, rgba(14, 63, 126, 0.04) 0px 24px 24px -12px",
        }}
        role="status"
        aria-label="Assistant is typing"
      >
        <div className="flex items-center gap-1">
          <span className="h-2 w-2 animate-bounce rounded-full bg-stone-400 dark:bg-stone-500" style={{ animationDelay: "0ms" }} />
          <span className="h-2 w-2 animate-bounce rounded-full bg-stone-400 dark:bg-stone-500" style={{ animationDelay: "150ms" }} />
          <span className="h-2 w-2 animate-bounce rounded-full bg-stone-400 dark:bg-stone-500" style={{ animationDelay: "300ms" }} />
        </div>
      </div>
    </div>
  )
}
