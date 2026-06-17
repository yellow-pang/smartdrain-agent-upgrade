"use client"

import { useState } from "react"
import { ChevronLeft, ChevronRight, Maximize2 } from "lucide-react"
import { cn } from "@/lib/utils"

const SNAPSHOTS = [
  "2024-05-23 14:30:00",
  "2024-05-23 14:00:00",
  "2024-05-23 13:30:00",
  "2024-05-23 13:00:00",
  "2024-05-23 12:30:00",
]

export function CctvSnapshotCard() {
  const [active, setActive] = useState(0)

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-bold text-slate-900">CCTV (상단뷰)</h2>
        <span className="text-xs text-slate-400">최근 캡처 · {SNAPSHOTS[active]}</span>
      </div>

      {/* main snapshot */}
      <div className="relative mt-3 aspect-[16/10] overflow-hidden rounded-lg border border-slate-200 bg-slate-900">
        <img
          src="/cctv-drain.png"
          alt="빗물받이 상단뷰 CCTV 스냅샷"
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
          {SNAPSHOTS.map((ts, i) => (
            <button
              key={ts}
              onClick={() => setActive(i)}
              className={cn(
                "aspect-square flex-1 overflow-hidden rounded-md border-2 transition-colors",
                active === i ? "border-cyan-600" : "border-transparent hover:border-slate-300",
              )}
              aria-label={`스냅샷 ${ts}`}
            >
              <img src="/cctv-drain.png" alt="" className="size-full object-cover grayscale" />
            </button>
          ))}
        </div>
        <button
          onClick={() => setActive((p) => Math.min(SNAPSHOTS.length - 1, p + 1))}
          className="flex size-8 shrink-0 items-center justify-center rounded-md border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-40"
          disabled={active === SNAPSHOTS.length - 1}
          aria-label="다음"
        >
          <ChevronRight className="size-4" />
        </button>
      </div>
    </div>
  )
}
