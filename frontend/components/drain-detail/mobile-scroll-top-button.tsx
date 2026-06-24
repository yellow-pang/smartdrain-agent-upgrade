"use client";

import { useEffect, useState } from "react";
import { ArrowUp } from "lucide-react";

const SCROLL_TOP_VISIBILITY_THRESHOLD = 480;

export function MobileScrollTopButton() {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        const updateVisibility = () => {
            setIsVisible(window.scrollY >= SCROLL_TOP_VISIBILITY_THRESHOLD);
        };

        updateVisibility();
        window.addEventListener("scroll", updateVisibility, { passive: true });

        return () => window.removeEventListener("scroll", updateVisibility);
    }, []);

    if (!isVisible) return null;

    return (
        <button
            type="button"
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
            className="fixed right-4 bottom-[calc(env(safe-area-inset-bottom)+5rem)] z-40 flex size-11 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-md transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-600 focus-visible:ring-offset-2 lg:hidden dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
            aria-label="상단으로 이동"
        >
            <ArrowUp className="size-5" />
        </button>
    );
}
