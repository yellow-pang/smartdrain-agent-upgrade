"use client";

import { useMemo, useState } from "react";
import { AlertCircle, Inbox, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";
import { STATUS_META, type DrainFacility } from "@/lib/mock-data";
import { StatusBadge } from "@/components/status-badge";
import { MetricProgress } from "@/components/metric-progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatDateTimeForDisplay } from "@/lib/date-format";

const SORT_OPTIONS = [
  { value: "risk", label: "위험도순" },
  { value: "recent", label: "최신순" },
  { value: "id", label: "시설 ID순" },
] as const;

type SortKey = (typeof SORT_OPTIONS)[number]["value"];
export type DrainRiskListStatus = "loading" | "success" | "empty" | "error";
export type DrainRealtimeStatus =
  | "waiting"
  | "connected"
  | "reconnecting"
  | "error";

export function DrainRiskList({
  drains,
  selectedId,
  onSelect,
  status = drains.length > 0 ? "success" : "empty",
  realtimeStatus = "waiting",
  onRetry,
}: {
  drains: DrainFacility[];
  selectedId?: string | null;
  onSelect?: (id: string) => void;
  status?: DrainRiskListStatus;
  realtimeStatus?: DrainRealtimeStatus;
  onRetry?: () => void;
}) {
  const [sort, setSort] = useState<SortKey>("risk");
  const isListReady = status === "success";

  const ordered = useMemo(() => {
    const list = [...drains];
    if (sort === "recent")
      return list.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
    if (sort === "id") return list.sort((a, b) => a.id.localeCompare(b.id));
    return list; // already risk-sorted from parent
  }, [drains, sort]);

  return (
    <div className="flex h-full flex-col rounded-xl border border-slate-200 bg-white">
      <div className="border-b border-slate-100 px-4 py-3 md:px-5 md:py-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-bold text-slate-900">위험 시설 목록</h2>
          <RealtimeStatusChip status={realtimeStatus} />
        </div>
        <div className="mt-3 flex justify-end">
          <Select
            value={sort}
            onValueChange={(v) => setSort(v as SortKey)}
            disabled={!isListReady}
          >
            <SelectTrigger className="h-8 w-30 border-slate-200 text-xs">
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
      </div>

      {status === "loading" && <DrainRiskListSkeleton />}
      {status === "empty" && <DrainRiskListEmptyState />}
      {status === "error" && <DrainRiskListErrorState onRetry={onRetry} />}
      {status === "success" && (
        <ul className="flex-1 divide-y divide-slate-100 overflow-y-auto">
          {ordered.map((drain, idx) => (
            <DrainRiskListItem
              key={drain.id}
              drain={drain}
              rank={idx + 1}
              selected={drain.id === selectedId}
              onSelect={onSelect}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

function DrainRiskListItem({
  drain,
  rank,
  selected,
  onSelect,
}: {
  drain: DrainFacility;
  rank: number;
  selected: boolean;
  onSelect?: (id: string) => void;
}) {
  const meta = STATUS_META[drain.status];

  return (
    <li>
      <button
        onClick={() => onSelect?.(drain.id)}
        className={cn(
          "w-full px-4 py-3 text-left transition-colors hover:bg-slate-50 md:px-5 md:py-4",
          selected && "bg-red-50/60 hover:bg-red-50/60",
        )}
      >
        <div className="flex items-start gap-2.5 md:items-center md:gap-3">
          <span
            className={cn(
              "mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-md text-xs font-bold text-white md:mt-0",
              meta.dot,
            )}
          >
            {rank}
          </span>
          <span className="shrink-0 font-semibold text-slate-900">
            {drain.id}
          </span>
          <span className="min-w-0 flex-1 text-sm text-slate-500 break-words [display:-webkit-box] [-webkit-box-orient:vertical] [-webkit-line-clamp:1] md:[-webkit-line-clamp:2] overflow-hidden">
            {drain.road}
          </span>
          <StatusBadge status={drain.status} className="ml-auto shrink-0" />
        </div>

        <div className="mt-2.5 flex flex-wrap items-center gap-2.5 md:mt-3 md:flex-nowrap md:gap-4">
          <div className="flex flex-1 items-center gap-2">
            <span className="w-14 shrink-0 text-[11px] text-slate-500 md:text-xs">
              막힘 정도
            </span>
            <MetricProgress
              value={drain.blockage}
              barClass={meta.bar}
              className="flex-1"
            />
            <span className="w-9 shrink-0 text-right text-[11px] font-semibold text-slate-700 md:text-xs">
              {drain.blockage}%
            </span>
          </div>
          <div className="flex shrink-0 items-center gap-1.5">
            <span className="text-[11px] text-slate-500 md:text-xs">수위</span>
            <span className="text-[11px] font-semibold text-slate-700 md:text-xs">
              {drain.waterLevelPct}%
            </span>
          </div>
        </div>

        <p className="mt-2 text-[11px] text-slate-400 md:text-xs">
          최근 업데이트{" "}
          <span className="text-slate-500">
            {formatDateTimeForDisplay(drain.updatedAt)}
          </span>
        </p>
      </button>
    </li>
  );
}

function RealtimeStatusChip({ status }: { status: DrainRealtimeStatus }) {
  const meta: Record<
    DrainRealtimeStatus,
    { label: string; className: string }
  > = {
    connected: {
      label: "실시간 연결됨",
      className: "border-emerald-200 bg-emerald-50 text-emerald-600",
    },
    waiting: {
      label: "실시간 연결 대기",
      className: "border-slate-200 bg-slate-100 text-slate-600",
    },
    reconnecting: {
      label: "재연결 중",
      className: "border-amber-200 bg-amber-50 text-amber-600",
    },
    error: {
      label: "연결 실패",
      className: "border-red-200 bg-red-50 text-red-600",
    },
  };

  return (
    <Badge className={cn("gap-1.5", meta[status].className)}>
      <span className="size-1.5 rounded-full bg-current" />
      {meta[status].label}
    </Badge>
  );
}

function DrainRiskListSkeleton() {
  return (
    <div className="flex-1 divide-y divide-slate-100 overflow-hidden">
      {Array.from({ length: 6 }, (_, index) => (
        <div key={index} className="px-5 py-4">
          <div className="flex animate-pulse items-center gap-3">
            <span className="size-6 rounded-md bg-slate-200" />
            <span className="h-4 w-16 rounded bg-slate-200" />
            <span className="h-4 flex-1 rounded bg-slate-100" />
            <span className="h-5 w-12 rounded-md bg-slate-100" />
          </div>
          <div className="mt-3 flex animate-pulse items-center gap-2">
            <span className="h-3 w-14 rounded bg-slate-100" />
            <span className="h-2 flex-1 rounded-full bg-slate-100" />
            <span className="h-3 w-8 rounded bg-slate-100" />
          </div>
          <div className="mt-2 h-3 w-36 animate-pulse rounded bg-slate-100" />
        </div>
      ))}
    </div>
  );
}

function DrainRiskListEmptyState() {
  return (
    <div className="flex flex-1 items-center justify-center px-5 py-10 text-center">
      <div>
        <span className="mx-auto flex size-10 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
          <Inbox className="size-5" />
        </span>
        <p className="mt-3 text-sm font-bold text-slate-800">
          현재 표시할 위험 시설이 없습니다.
        </p>
        <p className="mt-1 text-xs text-slate-500">
          모든 시설이 정상 상태이거나 조회된 시설이 없습니다.
        </p>
      </div>
    </div>
  );
}

function DrainRiskListErrorState({ onRetry }: { onRetry?: () => void }) {
  return (
    <div className="flex flex-1 items-center justify-center px-5 py-10">
      <div className="w-full rounded-lg border border-red-100 bg-red-50/60 p-4 text-center">
        <span className="mx-auto flex size-10 items-center justify-center rounded-lg bg-white text-red-500 shadow-sm">
          <AlertCircle className="size-5" />
        </span>
        <p className="mt-3 text-sm font-bold text-red-700">
          시설 목록을 불러오지 못했습니다.
        </p>
        <p className="mt-1 text-xs text-red-600/80">
          서버 연결을 확인한 뒤 다시 시도해주세요.
        </p>
        {onRetry && (
          <Button
            onClick={onRetry}
            size="sm"
            variant="outline"
            className="mt-4 border-red-200 bg-white text-red-600 hover:bg-red-50"
          >
            <RotateCcw className="size-3.5" />
            다시 시도
          </Button>
        )}
      </div>
    </div>
  );
}
