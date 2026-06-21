"use client";

import Link from "next/link";
import { memo, useCallback, useEffect, useMemo } from "react";
import { AlertCircle, ChevronRight, Info, RotateCcw } from "lucide-react";
import { AppHeader } from "@/components/app-header";
import { DrainMapPanel as RiskMap } from "@/components/dashboard/drain-map-panel";
import {
  DrainRiskList,
  type DrainRealtimeStatus,
  type DrainRiskListStatus,
} from "@/components/dashboard/drain-risk-list";
import { DrainDetailPanel as DrainSummaryPanel } from "@/components/dashboard/drain-detail-panel";
import { PlaceholderState } from "@/components/placeholder-state";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import type { DashboardSummaryDto } from "@/lib/api/types";
import { PLACEHOLDER_IMAGES } from "@/lib/placeholders";
import { formatDateTimeForDisplay } from "@/lib/date-format";
import { useDrainStore } from "@/store/drain-store";
import {
  useDashboardSummaryQuery,
  useDrainsQuery,
} from "@/lib/query/drain-queries";
import { sortFacilitiesByRisk } from "@/lib/api/adapters";
import type { DrainFacility } from "@/lib/mock-data";

export default function DashboardPage() {
  const drainsQuery = useDrainsQuery();
  const summaryQuery = useDashboardSummaryQuery();
  const selectedId = useDrainStore((state) => state.selectedDrainId);
  const setSelectedId = useDrainStore((state) => state.selectDrain);
  const realtimeStatus = useDrainStore((state) => state.socketStatus);
  const handleSelectDrain = useCallback(
    (id: string) => {
      setSelectedId(id);
    },
    [setSelectedId],
  );
  const isLoading = drainsQuery.isLoading;
  const dashboardData = useMemo(() => {
    if (!drainsQuery.data) return null;
    return {
      drains: drainsQuery.data,
      sortedDrains: sortFacilitiesByRisk(drainsQuery.data),
    };
  }, [drainsQuery.data]);
  const reloadDashboard = () => {
    void drainsQuery.refetch();
    void summaryQuery.refetch();
  };

  const selected = useMemo(() => {
    if (!dashboardData || !selectedId) {
      return undefined;
    }
    return dashboardData.drains.find((drain) => drain.id === selectedId);
  }, [dashboardData, selectedId]);

  const sorted = dashboardData?.sortedDrains ?? [];
  const effectiveSelectedId =
    selectedId && sorted.some((drain) => drain.id === selectedId)
      ? selectedId
      : (sorted[0]?.id ?? null);

  useEffect(() => {
    if (effectiveSelectedId !== selectedId) {
      setSelectedId(effectiveSelectedId);
    }
  }, [effectiveSelectedId, selectedId, setSelectedId]);

  const effectiveSelected =
    selected ??
    (effectiveSelectedId
      ? sorted.find((drain) => drain.id === effectiveSelectedId)
      : undefined);
  const riskListStatus = getRiskListStatus({
    dashboardData,
    isLoading,
  });
  const riskListRealtimeStatus: DrainRealtimeStatus =
    riskListStatus === "error"
      ? "error"
      : riskListStatus === "loading"
        ? "waiting"
        : realtimeStatus;

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <AppHeader />

      <main className="mx-auto w-full max-w-[1600px] flex-1 p-4 md:p-6">
        {summaryQuery.isLoading ? (
          <DashboardSummarySkeleton />
        ) : summaryQuery.data ? (
          <DashboardSummaryBar summary={summaryQuery.data} />
        ) : (
          <DashboardSummaryErrorState onRetry={reloadDashboard} />
        )}

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
          {/* Map */}
          <section className="lg:col-span-6 xl:col-span-7 xl:h-[clamp(32rem,calc(100dvh-11rem),42rem)] 2xl:h-[clamp(34rem,calc(100dvh-10rem),46rem)]">
            <div className="flex h-full flex-col rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 md:p-5">
              <div className="mb-4 flex items-center justify-between gap-3">
                <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  도시 배수 시설 위험도 지도
                </h2>
                {!dashboardData && (
                  <span className="text-xs font-medium text-slate-400 dark:text-slate-500">
                    데이터 불러오는 중
                  </span>
                )}
              </div>
              <div className="min-h-0 flex-1">
                {dashboardData ? (
                  <RiskMap
                    drains={dashboardData.drains}
                    selectedId={effectiveSelectedId}
                    onSelect={handleSelectDrain}
                    labelLocation={effectiveSelected?.road}
                  />
                ) : (
                  <MapLoadingState />
                )}
              </div>
              <p className="mt-3 flex items-center gap-1.5 text-xs text-slate-400 dark:text-slate-500">
                <Info className="size-3.5" />
                지도에서 배수 시설을 클릭하면 상세 정보를 확인할 수 있습니다.
              </p>
            </div>
          </section>

          {/* Risk list */}
          <section className="lg:col-span-6 xl:col-span-5 xl:h-[clamp(32rem,calc(100dvh-11rem),42rem)] 2xl:col-span-3 2xl:h-[clamp(34rem,calc(100dvh-10rem),46rem)]">
            <div className="h-full shadow-sm">
              <DrainRiskList
                drains={sorted}
                selectedId={effectiveSelectedId}
                onSelect={handleSelectDrain}
                status={riskListStatus}
                realtimeStatus={riskListRealtimeStatus}
                onRetry={reloadDashboard}
              />
            </div>
          </section>

          {/* Inline summary for mobile/tablet */}
          <section className="lg:col-span-12 xl:hidden">
            {effectiveSelected ? (
              <MobileDrainInlineSummary drain={effectiveSelected} />
            ) : !isLoading && sorted.length === 0 ? (
              <PlaceholderState
                image={PLACEHOLDER_IMAGES.facility}
                title="선택된 시설이 없습니다"
                description="지도 또는 목록에서 시설을 선택하면 요약 정보를 확인할 수 있습니다."
                statusLabel="시설 미선택"
                className="min-h-[180px]"
              />
            ) : null}
          </section>

          {/* Detail panel */}
          <section className="hidden xl:col-span-12 xl:block 2xl:col-span-2 2xl:h-[clamp(34rem,calc(100dvh-10rem),46rem)]">
            {effectiveSelected ? (
              <div className="h-full shadow-sm">
                <DrainSummaryPanel drain={effectiveSelected} />
              </div>
            ) : !isLoading && sorted.length === 0 ? (
              <PlaceholderState
                image={PLACEHOLDER_IMAGES.facility}
                title="상세 정보를 불러올 수 없습니다"
                description="백엔드 연결을 확인한 뒤 다시 시도해주세요."
                statusLabel="연결 오류"
                className="min-h-[420px]"
              />
            ) : null}
          </section>
        </div>
      </main>
    </div>
  );
}

const MobileDrainInlineSummary = memo(function MobileDrainInlineSummary({
  drain,
}: {
  drain: DrainFacility;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
          선택 시설 요약
        </p>
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-xs text-slate-500 dark:text-slate-400">시설명</p>
            <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 [display:-webkit-box] [-webkit-box-orient:vertical] [-webkit-line-clamp:1] overflow-hidden">
              {drain.road}
            </p>
          </div>
          <StatusBadge status={drain.status} className="shrink-0" />
        </div>
        <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
          <div className="rounded-md bg-slate-50 px-2.5 py-2 dark:bg-slate-800/80">
            <p className="text-slate-500 dark:text-slate-400">막힘</p>
            <p className="mt-0.5 font-semibold text-slate-800 dark:text-slate-100">
              {drain.blockage}%
            </p>
          </div>
          <div className="rounded-md bg-slate-50 px-2.5 py-2 dark:bg-slate-800/80">
            <p className="text-slate-500 dark:text-slate-400">수위</p>
            <p className="mt-0.5 font-semibold text-slate-800 dark:text-slate-100">
              {drain.waterLevelPct}%
            </p>
          </div>
          <div className="rounded-md bg-slate-50 px-2.5 py-2 dark:bg-slate-800/80">
            <p className="text-slate-500 dark:text-slate-400">유량</p>
            <p className="mt-0.5 font-semibold text-slate-800 dark:text-slate-100">
              {drain.flow} m³/min
            </p>
          </div>
        </div>
        <p className="mt-2 text-[11px] text-slate-500 dark:text-slate-400">
          최근 업데이트 {formatDateTimeForDisplay(drain.updatedAt)}
        </p>
        <Button
          nativeButton={false}
          className="mt-2 h-9 w-full bg-cyan-700 text-white hover:bg-cyan-800"
          render={
            <Link href={`/drains/${drain.id}`}>
              상세 정보 페이지로 이동
              <ChevronRight className="size-4" />
            </Link>
          }
        />
      </div>
    </section>
  );
});

function getRiskListStatus({
  dashboardData,
  isLoading,
}: {
  dashboardData: {
    sortedDrains: import("@/lib/mock-data").DrainFacility[];
  } | null;
  isLoading: boolean;
}): DrainRiskListStatus {
  if (isLoading) return "loading";
  if (!dashboardData) return "error";
  if (dashboardData.sortedDrains.length === 0) return "empty";
  return "success";
}

function DashboardSummaryBar({ summary }: { summary: DashboardSummaryDto }) {
  const items = [
    { label: "전체", value: summary.totalCount, className: "text-slate-900" },
    { label: "위험", value: summary.dangerCount, className: "text-red-600" },
    {
      label: "주의",
      value: summary.cautionCount,
      className: "text-amber-600",
    },
    {
      label: "양호",
      value: summary.goodCount,
      className: "text-emerald-600",
    },
    {
      label: "판단불가",
      value: summary.unknownCount,
      className: "text-slate-500",
    },
  ];

  return (
    <section className="mb-4 rounded-xl border border-slate-200 bg-white px-4 py-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 md:px-5">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <p className="text-sm font-bold text-slate-900 dark:text-slate-100">
            대시보드 현황
          </p>
          <p className="mt-0.5 text-xs text-slate-500 break-words dark:text-slate-400">
            API 응답 기준
            {summary.latestUpdatedAt
              ? ` · 최신 업데이트 ${formatDateTimeForDisplay(summary.latestUpdatedAt)}`
              : ""}
          </p>
        </div>
        <dl className="grid w-full grid-cols-2 gap-2 sm:grid-cols-3 lg:w-auto lg:grid-cols-5">
          {items.map((item) => (
            <div
              key={item.label}
              className="rounded-lg bg-slate-50 px-3 py-2 text-center dark:bg-slate-800/80"
            >
              <dt className="text-xs text-slate-500 dark:text-slate-400">
                {item.label}
              </dt>
              <dd className={`mt-0.5 text-lg font-bold ${item.className}`}>
                {item.value}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}

function DashboardSummarySkeleton() {
  return (
    <section className="mb-4 rounded-xl border border-slate-200 bg-white px-4 py-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 md:px-5">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="h-4 w-24 animate-pulse rounded bg-slate-200" />
          <div className="mt-2 h-3 w-44 animate-pulse rounded bg-slate-100" />
        </div>
        <div className="grid w-full grid-cols-2 gap-2 sm:grid-cols-3 lg:w-auto lg:grid-cols-5">
          {Array.from({ length: 5 }, (_, index) => (
            <div key={index} className="rounded-lg bg-slate-50 px-3 py-2">
              <div className="mx-auto h-3 w-10 animate-pulse rounded bg-slate-100" />
              <div className="mx-auto mt-2 h-5 w-8 animate-pulse rounded bg-slate-200" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function DashboardSummaryErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <section className="mb-4 rounded-xl border border-red-100 bg-red-50/60 px-5 py-4 shadow-sm dark:border-red-950/60 dark:bg-red-950/30">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-white text-red-500 shadow-sm">
            <AlertCircle className="size-5" />
          </span>
          <div>
            <p className="text-sm font-bold text-red-700 dark:text-red-300">
              대시보드 현황을 불러오지 못했습니다.
            </p>
            <p className="mt-0.5 text-xs text-red-600/80 dark:text-red-300/80">
              실제 API 요약 데이터가 도착하면 현황 숫자가 표시됩니다.
            </p>
          </div>
        </div>
        <Button
          onClick={onRetry}
          size="sm"
          variant="outline"
          className="border-red-200 bg-white text-red-600 hover:bg-red-50"
        >
          <RotateCcw className="size-3.5" />
          다시 시도
        </Button>
      </div>
    </section>
  );
}

function MapLoadingState() {
  return (
    <div className="flex min-h-[280px] items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 text-center text-sm font-medium text-slate-400 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-500 sm:min-h-[320px] md:min-h-[420px]">
      배수 시설 데이터를 불러오고 있습니다.
    </div>
  );
}
