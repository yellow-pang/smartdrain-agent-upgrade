"use client"

import { Crosshair, Minus, Plus } from "lucide-react"
import { cn } from "@/lib/utils"
import { DRAINS, LEGEND_COUNTS, STATUS_META, type DrainFacility } from "@/lib/mock-data"

/**
 * Mock map component. Renders a stylised street grid background with
 * positioned facility markers. Replace the inner background + marker
 * positioning with a real map SDK (Kakao / Naver / Mapbox) later —
 * the public props (drains, selectedId, onSelect) stay the same.
 */
export function RiskMap({
  drains = DRAINS,
  selectedId,
  onSelect,
  labelLocation,
}: {
  drains?: DrainFacility[]
  selectedId?: string | null
  onSelect?: (id: string) => void
  labelLocation?: string
}) {
  return (
    <div className="relative h-full min-h-[420px] w-full overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
      <MockStreetBackground />

      {/* Legend */}
      <div className="absolute left-4 top-4 z-20 rounded-lg border border-slate-200 bg-white/95 px-3 py-2.5 shadow-sm backdrop-blur">
        <ul className="flex flex-col gap-1.5 text-xs font-medium text-slate-600">
          <LegendRow color={STATUS_META.danger.dot} label="위험" count={LEGEND_COUNTS.danger} />
          <LegendRow color={STATUS_META.warning.dot} label="주의" count={LEGEND_COUNTS.warning} />
          <LegendRow color={STATUS_META.normal.dot} label="정상" count={LEGEND_COUNTS.normal} />
        </ul>
      </div>

      {/* Mock controls */}
      <div className="absolute right-4 top-4 z-20 flex flex-col overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <button className="flex size-9 items-center justify-center text-slate-600 hover:bg-slate-50" aria-label="확대">
          <Plus className="size-4" />
        </button>
        <div className="h-px w-full bg-slate-200" />
        <button className="flex size-9 items-center justify-center text-slate-600 hover:bg-slate-50" aria-label="축소">
          <Minus className="size-4" />
        </button>
      </div>
      <div className="absolute right-4 top-[120px] z-20 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <button className="flex size-9 items-center justify-center text-slate-600 hover:bg-slate-50" aria-label="현재 위치">
          <Crosshair className="size-4" />
        </button>
      </div>

      {/* Markers */}
      {drains.map((drain) => {
        const selected = drain.id === selectedId
        const meta = STATUS_META[drain.status]
        return (
          <button
            key={drain.id}
            onClick={() => onSelect?.(drain.id)}
            className="absolute z-10 -translate-x-1/2 -translate-y-1/2 focus:outline-none"
            style={{ left: `${drain.x}%`, top: `${drain.y}%` }}
            aria-label={`${drain.id} ${drain.road}`}
          >
            {selected && (
              <>
                <span className="absolute left-1/2 top-1/2 size-10 -translate-x-1/2 -translate-y-1/2 animate-ping rounded-full bg-red-400/40" />
                <span className="absolute left-1/2 top-1/2 size-9 -translate-x-1/2 -translate-y-1/2 rounded-full bg-red-500/15 ring-2 ring-red-400" />
              </>
            )}
            <span
              className={cn(
                "relative block size-4 rounded-full border-2 border-white shadow-md transition-transform",
                meta.dot,
                selected ? "scale-125 ring-2 ring-red-500" : "hover:scale-110",
              )}
            />
            {selected && labelLocation && (
              <span className="absolute left-1/2 top-7 -translate-x-1/2 whitespace-nowrap rounded-md bg-slate-900 px-2 py-1 text-[11px] font-semibold text-white shadow-md">
                {labelLocation}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}

function LegendRow({ color, label, count }: { color: string; label: string; count: number }) {
  return (
    <li className="flex items-center gap-2">
      <span className={cn("size-2.5 rounded-full", color)} />
      <span>
        {label} ({count})
      </span>
    </li>
  )
}

function MockStreetBackground() {
  return (
    <svg
      className="absolute inset-0 h-full w-full"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <rect width="100%" height="100%" fill="#f1f5f9" />
      {/* blocks */}
      <defs>
        <pattern id="blocks" width="120" height="120" patternUnits="userSpaceOnUse">
          <rect width="120" height="120" fill="#f8fafc" />
          <rect x="8" y="8" width="104" height="104" rx="4" fill="#eef2f6" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#blocks)" />
      {/* roads */}
      {[15, 35, 55, 75].map((y) => (
        <line key={`h${y}`} x1="0" y1={`${y}%`} x2="100%" y2={`${y}%`} stroke="#e2e8f0" strokeWidth="10" />
      ))}
      {[20, 45, 70].map((x) => (
        <line key={`v${x}`} x1={`${x}%`} y1="0" x2={`${x}%`} y2="100%" stroke="#e2e8f0" strokeWidth="10" />
      ))}
      {/* diagonal main road */}
      <line x1="0" y1="100%" x2="100%" y2="20%" stroke="#dbe3ec" strokeWidth="14" />
      {/* river */}
      <path
        d="M 100 540 C 200 480, 260 520, 340 470 S 500 430, 620 460"
        fill="none"
        stroke="#cfe3f2"
        strokeWidth="16"
        strokeLinecap="round"
        opacity="0.8"
      />
    </svg>
  )
}
