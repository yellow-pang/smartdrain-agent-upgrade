"use client";

import { useState, type ComponentPropsWithoutRef } from "react";
import { PLACEHOLDER_IMAGES } from "@/lib/placeholders";

type FallbackImageProps = Omit<ComponentPropsWithoutRef<"img">, "src" | "alt"> & {
    src?: string;
    alt: string;
    fallbackSrc?: string;
};

export function FallbackImage({
    src,
    alt,
    fallbackSrc = PLACEHOLDER_IMAGES.thumbnail,
    onError,
    ...props
}: FallbackImageProps) {
    const [failedSrc, setFailedSrc] = useState<string | null>(null);
    const safeSrc = getSafeImageSource(src);
    const safeFallbackSrc =
        getSafeImageSource(fallbackSrc) ?? PLACEHOLDER_IMAGES.thumbnail;
    const currentSrc = safeSrc && safeSrc !== failedSrc ? safeSrc : safeFallbackSrc;

    return (
        <img
            {...props}
            src={currentSrc}
            alt={alt}
            onError={(event) => {
                if (safeSrc && safeSrc !== safeFallbackSrc) {
                    setFailedSrc(safeSrc);
                }
                onError?.(event);
            }}
        />
    );
}

function getSafeImageSource(src?: string) {
    if (!src) return undefined;
    if (src.startsWith("/") && !src.startsWith("//")) return src;

    try {
        const url = new URL(src);
        return url.protocol === "https:" || url.protocol === "http:"
            ? url.href
            : undefined;
    } catch {
        return undefined;
    }
}
