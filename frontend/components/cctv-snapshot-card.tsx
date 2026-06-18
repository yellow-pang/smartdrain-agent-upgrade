"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, Maximize2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { PLACEHOLDER_IMAGES } from "@/lib/placeholders";
import { FallbackImage } from "@/components/fallback-image";

type Snapshot = {
    imageUrl: string;
    capturedAt: string;
};

export function CctvSnapshotCard({
    snapshots,
    locationName,
}: {
    snapshots: Snapshot[];
    locationName: string;
}) {
    const [active, setActive] = useState(0);
    const safeSnapshots =
        snapshots.length > 0
            ? snapshots
            : [
                  {
                      imageUrl: PLACEHOLDER_IMAGES.cctv,
                      capturedAt: "분석 데이터 없음",
                  },
              ];
    const current = safeSnapshots[Math.min(active, safeSnapshots.length - 1)];

    return (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
                <h2 className="text-base font-bold text-slate-900">
                    CCTV (상단뷰)
                </h2>
                <span className="text-xs text-slate-400">
                    최근 캡처 · {current.capturedAt}
                </span>
            </div>

            {/* main snapshot */}
            <div className="relative mt-3 aspect-[16/10] overflow-hidden rounded-lg border border-slate-200 bg-slate-900">
                <FallbackImage
                    src={current.imageUrl}
                    fallbackSrc={PLACEHOLDER_IMAGES.cctv}
                    alt={`${locationName} 빗물받이 상단뷰 CCTV 스냅샷`}
                    className="size-full object-cover grayscale"
                />
                <button
                    className="absolute right-2 top-2 flex size-8 items-center justify-center rounded-md bg-black/45 text-white hover:bg-black/60"
                    aria-label="확대"
                >
                    <Maximize2 className="size-4" />
                </button>
            </div>

            {/* thumbnails */}
            <div className="mt-3 flex items-center gap-2">
                <button
                    onClick={() => setActive((p) => Math.max(0, p - 1))}
                    className="flex size-8 shrink-0 items-center justify-center rounded-md border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-40"
                    disabled={active === 0}
                    aria-label="이전"
                >
                    <ChevronLeft className="size-4" />
                </button>
                <div className="flex flex-1 gap-2">
                    {safeSnapshots.map((snapshot, i) => (
                        <button
                            key={`${snapshot.capturedAt}-${i}`}
                            onClick={() => setActive(i)}
                            className={cn(
                                "aspect-square flex-1 overflow-hidden rounded-md border-2 transition-colors",
                                active === i
                                    ? "border-cyan-600"
                                    : "border-transparent hover:border-slate-300",
                            )}
                            aria-label={`스냅샷 ${snapshot.capturedAt}`}
                        >
                            <FallbackImage
                                src={snapshot.imageUrl}
                                fallbackSrc={PLACEHOLDER_IMAGES.thumbnail}
                                alt=""
                                className="size-full object-cover grayscale"
                            />
                        </button>
                    ))}
                </div>
                <button
                    onClick={() =>
                        setActive((p) =>
                            Math.min(safeSnapshots.length - 1, p + 1),
                        )
                    }
                    className="flex size-8 shrink-0 items-center justify-center rounded-md border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-40"
                    disabled={active === safeSnapshots.length - 1}
                    aria-label="다음"
                >
                    <ChevronRight className="size-4" />
                </button>
            </div>
        </div>
    );
}
