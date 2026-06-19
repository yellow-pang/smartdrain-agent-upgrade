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
    const currentSrc = src && src !== failedSrc ? src : fallbackSrc;

    return (
        <img
            {...props}
            src={currentSrc}
            alt={alt}
            onError={(event) => {
                if (src && src !== fallbackSrc) {
                    setFailedSrc(src);
                }
                onError?.(event);
            }}
        />
    );
}
