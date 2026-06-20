"use client";

import { useEffect } from "react";
import { X } from "lucide-react";
import { FallbackImage } from "@/components/fallback-image";

export function ImagePreviewDialog({
    open,
    onClose,
    src,
    fallbackSrc,
    alt,
}: {
    open: boolean;
    onClose: () => void;
    src: string;
    fallbackSrc: string;
    alt: string;
}) {
    useEffect(() => {
        if (!open) return;

        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") onClose();
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [onClose, open]);

    if (!open) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4"
            role="presentation"
            onClick={onClose}
        >
            <section
                className="relative max-h-full w-full max-w-5xl overflow-hidden rounded-xl bg-slate-950 shadow-2xl"
                role="dialog"
                aria-modal="true"
                aria-label="CCTV 이미지 확대 보기"
                onClick={(event) => event.stopPropagation()}
            >
                <FallbackImage
                    src={src}
                    fallbackSrc={fallbackSrc}
                    alt={alt}
                    className="max-h-[85vh] w-full object-contain"
                />
                <button
                    type="button"
                    className="absolute right-3 top-3 flex size-9 items-center justify-center rounded-full bg-black/60 text-white hover:bg-black/80 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
                    onClick={onClose}
                    aria-label="확대 이미지 닫기"
                >
                    <X className="size-5" />
                </button>
            </section>
        </div>
    );
}
