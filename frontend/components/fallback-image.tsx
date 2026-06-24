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
    if (src.startsWith("//")) return undefined;
    if (src.startsWith("/")) return src;
    if (!hasUrlScheme(src)) return src;

    try {
        const url = new URL(src);
        if (
            url.protocol === "https:" ||
            url.protocol === "http:" ||
            url.protocol === "blob:"
        ) {
            return url.href;
        }

        return isSafeImageDataUrl(src) ? src : undefined;
    } catch {
        return undefined;
    }
}

function hasUrlScheme(value: string) {
    return /^[a-z][a-z\d+.-]*:/i.test(value);
}

function isSafeImageDataUrl(value: string) {
    return /^data:image\/(?:avif|gif|jpe?g|png|webp);base64,/i.test(value);
}
