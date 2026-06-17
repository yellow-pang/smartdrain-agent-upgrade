"use client"

import { useMemo, useState } from "react"
import { cn } from "@/lib/utils"
import { STATUS_META, type DrainFacility } from "@/lib/mock-data"
import { StatusBadge } from "@/components/status-badge"
import { MetricProgress } from "@/components/metric-progress"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const SORT_OPTIONS = [
  { value: "risk", label: "위험도순" },
  { value: "recent", label: "최신순" },
  { value: "id", label: "시설 ID순" },
] as const

type SortKey = (typeof SORT_OPTIONS)[number]["value"]

export function DrainRiskList({
  drains,
  selectedId,
  onSelect,
}: {
  drains: DrainFacility[]
  selectedId?: string | null
  onSelect?: (id: string) => void
}) {
  const [sort, setSort] = useState<SortKey>("risk")

  const ordered = useMemo(() => {
    const list = [...drains]
    if (sort === "recent") return list.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
    if (sort === "id") return list.sort((a, b) => a.id.localeCompare(b.id))
    return list // already risk-sorted from parent
  }, [drains, sort])

  return (
    <div className="flex h-full flex-col rounded-xl border border-slate-200 bg-white">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <h2 className="text-base font-bold text-slate-900">위험 시설 목록</h2>
        <Select value={sort} onValueChange={(v) => setSort(v as SortKey)}>
          <SelectTrigger className="h-8 w-28 border-slate-200 text-xs">
            <SelectValue placeholder="정렬">
              {SORT_OPTIONS.find((o) => o.value === sort)?.label}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {SORT_OPTIONS.map((o) => (
              <SelectItem key={o.value} value={o.value}>
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <ul className="flex-1 divide-y divide-slate-100 overflow-y-auto">
        {ordered.map((drain, idx) => {
          const meta = STATUS_META[drain.status]
          const selected = drain.id === selectedId
          return (
            <li key={drain.id}>
              <button
                onClick={() => onSelect?.(drain.id)}
                className={cn(
                  "w-full px-5 py-4 text-left transition-colors hover:bg-slate-50",
                  selected && "bg-red-50/60 hover:bg-red-50/60",
                )}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={cn(
                      "flex size-6 shrink-0 items-center justify-center rounded-md text-xs font-bold text-white",
                      meta.dot,
                    )}
                  >
                    {idx + 1}
                  </span>
                  <span className="font-semibold text-slate-900">{drain.id}</span>
                  <span className="truncate text-sm text-slate-500">{drain.road}</span>
                  <StatusBadge status={drain.status} className="ml-auto" />
                </div>

                <div className="mt-3 flex items-center gap-4">
                  <div className="flex flex-1 items-center gap-2">
                    <span className="w-14 shrink-0 text-xs text-slate-500">막힘 정도</span>
                    <MetricProgress value={drain.blockage} barClass={meta.bar} className="flex-1" />
                    <span className="w-9 shrink-0 text-right text-xs font-semibold text-slate-700">
                      {drain.blockage}%
                    </span>
                  </div>
                  <div className="flex shrink-0 items-center gap-1.5">
                    <span className="text-xs text-slate-500">수위</span>
                    <span className="text-xs font-semibold text-slate-700">{drain.waterLevelPct}%</span>
                  </div>
                </div>

                <p className="mt-2 text-xs text-slate-400">
                  최근 업데이트 <span className="text-slate-500">{drain.updatedAt}</span>
                </p>
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
