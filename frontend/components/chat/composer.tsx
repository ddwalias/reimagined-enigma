"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { ArrowUp, Mic, MicOff, Square } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

import { AudioWaveform } from "./audio-waveform";

interface ComposerProps {
  onSend: (content: string) => void;
  onStop: () => void;
  isStreaming: boolean;
  disabled?: boolean;
}

export function Composer({
  onSend,
  onStop,
  isStreaming,
  disabled,
}: ComposerProps) {
  const [value, setValue] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [hasAnimated, setHasAnimated] = useState(false);
  const [mediaStream, setMediaStream] = useState<MediaStream | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<any>(null);
  const baseTextRef = useRef("");
  const finalTranscriptsRef = useRef("");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        (window as any).SpeechRecognition ||
        (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = true;
        recognitionRef.current.interimResults = true;
        recognitionRef.current.lang = "en-US";

        recognitionRef.current.onresult = (event: any) => {
          let newFinalText = "";
          for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
              newFinalText += `${event.results[i][0].transcript} `;
            }
          }

          if (newFinalText) {
            finalTranscriptsRef.current += newFinalText;
            setValue(baseTextRef.current + finalTranscriptsRef.current);
            setTimeout(() => handleInput(), 0);
          }
        };

        recognitionRef.current.onerror = () => {
          setIsRecording(false);
        };

        recognitionRef.current.onend = () => {
          setIsRecording(false);
        };
      }
    }

    return () => {
      recognitionRef.current?.stop();
    };
  }, []);

  useEffect(() => {
    setHasAnimated(true);
  }, []);

  const playClickSound = useCallback(() => {
    const audio = new Audio(
      "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/click-FM4Xaa1FJj237591TiZw4yL1fIxdOw.mp3",
    );
    audio.volume = 0.5;
    audio.play().catch(() => {});
  }, []);

  const playRecordSound = useCallback(() => {
    const audio = new Audio(
      "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/record-CNHOyjcpri6lx5C2sGXncDtFVDwspO.mp3",
    );
    audio.volume = 0.5;
    audio.play().catch(() => {});
  }, []);

  const handleInput = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  }, []);

  const toggleRecording = useCallback(() => {
    playClickSound();

    if (!recognitionRef.current) {
      window.alert("Speech recognition is not supported in your browser");
      return;
    }

    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
      mediaStream?.getTracks().forEach((track) => track.stop());
      setMediaStream(null);
      return;
    }

    playRecordSound();
    baseTextRef.current = value;
    finalTranscriptsRef.current = "";
    recognitionRef.current.start();
    setIsRecording(true);

    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => setMediaStream(stream))
      .catch((err) => {
        console.error("Error getting microphone stream:", err);
      });
  }, [isRecording, mediaStream, playClickSound, playRecordSound, value]);

  const handleSend = useCallback(() => {
    if (!value.trim() || isStreaming || disabled) return;
    playClickSound();

    if (isRecording && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }

    onSend(value);
    setValue("");
    baseTextRef.current = "";
    finalTranscriptsRef.current = "";
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [disabled, isRecording, isStreaming, onSend, playClickSound, value]);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLTextAreaElement>) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  return (
    <div
      className={cn(
        "pointer-events-none fixed bottom-4 left-0 right-0 z-10 px-4",
        hasAnimated && "composer-intro",
      )}
    >
      <div className="relative mx-auto max-w-2xl pointer-events-auto">
        <div
          className={cn(
            "relative flex flex-col gap-3 overflow-hidden rounded-3xl border border-stone-200 bg-white/95 p-4 transition-all duration-200 backdrop-blur",
            "focus-within:border-stone-300 focus-within:ring-2 focus-within:ring-stone-200/80 dark:border-stone-800 dark:bg-stone-900/95 dark:focus-within:border-stone-700 dark:focus-within:ring-stone-700/70",
          )}
          style={{
            boxShadow:
              "rgba(14, 63, 126, 0.06) 0px 0px 0px 1px, rgba(42, 51, 69, 0.06) 0px 1px 1px -0.5px, rgba(42, 51, 70, 0.06) 0px 3px 3px -1.5px, rgba(42, 51, 70, 0.06) 0px 6px 6px -3px, rgba(14, 63, 126, 0.06) 0px 12px 12px -6px, rgba(14, 63, 126, 0.06) 0px 24px 24px -12px",
          }}
        >
          <div className="flex items-center gap-2">
            <textarea
              ref={textareaRef}
              value={value}
              onChange={(event) => {
                setValue(event.target.value);
                handleInput();
              }}
              onKeyDown={handleKeyDown}
              placeholder={
                isRecording
                  ? "Listening..."
                  : "Ask OptiBot about OptiSigns support docs..."
              }
              disabled={isStreaming || disabled}
              rows={1}
              className={cn(
                "max-h-[56px] flex-1 resize-none overflow-y-auto bg-transparent px-2 py-1.5 text-sm text-stone-900 caret-stone-900",
                "placeholder:text-stone-500 focus:outline-none disabled:cursor-not-allowed disabled:text-stone-500 dark:text-stone-100 dark:caret-stone-100 dark:placeholder:text-stone-400 dark:disabled:text-stone-500",
              )}
              aria-label="Message input"
            />

            {isRecording && (
              <div className="w-24 shrink-0">
                <AudioWaveform isRecording={isRecording} stream={mediaStream} />
              </div>
            )}

            {isStreaming ? (
              <button
                onClick={() => {
                  playClickSound();
                  onStop();
                }}
                className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-red-400/70 bg-red-500 text-white shadow-sm transition-all hover:scale-105 hover:bg-red-400 dark:border-red-400 dark:bg-red-500 dark:text-white dark:hover:bg-red-400"
                aria-label="Stop generating"
              >
                <Square className="h-3.5 w-3.5" fill="currentColor" aria-hidden="true" />
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!value.trim() || disabled}
                className={cn(
                  "relative flex h-9 w-9 shrink-0 items-center justify-center rounded-full border transition-all",
                  !value.trim() || disabled
                    ? "cursor-not-allowed border-stone-200 bg-stone-100 text-stone-500 dark:border-stone-700 dark:bg-stone-800 dark:text-stone-500"
                    : "cursor-pointer border-stone-900 bg-stone-900 text-white hover:scale-105 hover:bg-stone-800 dark:border-emerald-400 dark:bg-emerald-400 dark:text-stone-950 dark:hover:bg-emerald-300",
                )}
                aria-label="Send message"
              >
                <ArrowUp className="h-4 w-4" />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <div className="relative">
              <Button
                onClick={toggleRecording}
                disabled={isStreaming || disabled}
                size="icon"
                className={cn(
                  "relative z-10 h-9 w-9 shrink-0 rounded-full border border-stone-200 transition-all",
                  isRecording
                    ? "animate-bounce border-red-500 bg-red-500 text-white hover:bg-red-600"
                    : "bg-stone-100 text-stone-700 hover:bg-stone-200 dark:border-stone-700 dark:bg-stone-800 dark:text-stone-200 dark:hover:bg-stone-700",
                )}
                aria-label={
                  isRecording ? "Stop recording" : "Start voice input"
                }
              >
                {isRecording ? (
                  <MicOff className="h-4 w-4" />
                ) : (
                  <Mic className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
