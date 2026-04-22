"use client"

import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import { cn } from "@/lib/utils"

interface MarkdownRendererProps {
  content: string
  className?: string
  isStreaming?: boolean
}

const INLINE_CODE_CLASS_NAME =
  "rounded bg-stone-100 px-1.5 py-0.5 font-mono text-[0.9em] text-stone-700 dark:bg-stone-800 dark:text-stone-200"

export function MarkdownRenderer({ content, className, isStreaming = false }: MarkdownRendererProps) {
  if (!content.trim()) {
    return <div className={cn("min-h-5 text-sm", className)} />
  }

  return (
    <div
      className={cn(
        "space-y-4 break-words text-sm text-stone-900 dark:text-stone-100",
        isStreaming && "transition-opacity duration-200",
        className,
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => <p className="leading-7">{children}</p>,
          ul: ({ children }) => <ul className="list-disc space-y-2 pl-5 leading-7">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal space-y-2 pl-5 leading-7">{children}</ol>,
          li: ({ children }) => <li>{children}</li>,
          h1: ({ children }) => <h1 className="text-2xl font-semibold tracking-tight">{children}</h1>,
          h2: ({ children }) => <h2 className="text-xl font-semibold tracking-tight">{children}</h2>,
          h3: ({ children }) => <h3 className="text-lg font-semibold">{children}</h3>,
          h4: ({ children }) => <h4 className="text-base font-semibold">{children}</h4>,
          strong: ({ children }) => <strong className="font-semibold text-stone-950 dark:text-white">{children}</strong>,
          em: ({ children }) => <em className="italic text-stone-800 dark:text-stone-200">{children}</em>,
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-600 underline underline-offset-2 transition-colors hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
            >
              {children}
            </a>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-stone-300 pl-4 italic text-stone-600 dark:border-stone-700 dark:text-stone-300">
              {children}
            </blockquote>
          ),
          code: ({ className: codeClassName, children }) => {
            const languageMatch = /language-(\w+)/.exec(codeClassName || "")
            const isBlock = Boolean(languageMatch)

            if (!isBlock) {
              return <code className={INLINE_CODE_CLASS_NAME}>{children}</code>
            }

            return (
              <code className="font-mono text-sm text-stone-100 dark:text-stone-200">
                {String(children).replace(/\n$/, "")}
              </code>
            )
          },
          pre: ({ children }) => (
            <pre
              className="overflow-x-auto rounded-lg bg-stone-900 p-3 text-sm dark:bg-stone-950"
              style={{
                boxShadow:
                  "rgba(14, 63, 126, 0.04) 0px 0px 0px 1px, rgba(42, 51, 69, 0.04) 0px 1px 1px -0.5px, rgba(42, 51, 70, 0.04) 0px 3px 3px -1.5px, rgba(42, 51, 70, 0.04) 0px 6px 6px -3px, rgba(14, 63, 126, 0.04) 0px 12px 12px -6px, rgba(14, 63, 126, 0.04) 0px 24px 24px -12px",
              }}
            >
              {children}
            </pre>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
