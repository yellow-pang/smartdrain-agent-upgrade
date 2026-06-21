"use client";

import { useEffect, useRef } from "react";

export function ComingSoonPopover({
  message,
  onClose,
  align = "start",
}: {
  message: string;
  onClose: () => void;
  align?: "start" | "end";
}) {
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timeoutId = window.setTimeout(onClose, 2500);
    const handlePointerDown = (event: PointerEvent) => {
      if (!popoverRef.current?.contains(event.target as Node)) {
        onClose();
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      window.clearTimeout(timeoutId);
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  return (
    <div
      ref={popoverRef}
      role="status"
      aria-live="polite"
      className={`absolute top-11 z-50 w-max max-w-[min(18rem,calc(100vw-1.5rem))] rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-600 shadow-lg dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 ${align === "end" ? "right-0" : "left-0"}`}
    >
      {message}
    </div>
  );
}
