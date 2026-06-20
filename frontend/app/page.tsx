"use client";

import { useMemo } from "react";
import { AlertCircle, Info, RotateCcw } from "lucide-react";
import { AppHeader } from "@/components/app-header";
import { DrainMapPanel as RiskMap } from "@/components/dashboard/drain-map-panel";
import {
    DrainRiskList,
    type DrainRealtimeStatus,
    type DrainRiskListStatus,
} from "@/components/dashboard/drain-risk-list";
import { DrainDetailPanel as DrainSummaryPanel } from "@/components/dashboard/drain-detail-panel";
import { PlaceholderState } from "@/components/placeholder-state";
import { Button } from "@/components/ui/button";
import type { DashboardSummaryDto } from "@/lib/api/types";
import { PLACEHOLDER_IMAGES } from "@/lib/placeholders";
import { useDrainStore } from "@/store/drain-store";
import { useDashboardSummaryQuery, useDrainsQuery } from "@/lib/query/drain-queries";
import { sortFacilitiesByRisk } from "@/lib/api/adapters";

export default function DashboardPage() {
    const drainsQuery = useDrainsQuery();
    const summaryQuery = useDashboardSummaryQuery();
    const selectedId = useDrainStore((state) => state.selectedDrainId);
    const setSelectedId = useDrainStore((state) => state.selectDrain);
    const realtimeStatus = useDrainStore((state) => state.socketStatus);
    const isLoading = drainsQuery.isLoading || summaryQuery.isLoading;
    const dashboardData = useMemo(() => {
        if (!drainsQuery.data || !summaryQuery.data) return null;
        return { drains: drainsQuery.data, sortedDrains: sortFacilitiesByRisk(drainsQuery.data), summary: summaryQuery.data };
    }, [drainsQuery.data, summaryQuery.data]);
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

    const sorted =
        dashboardData?.sortedDrains ?? [];
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
        <div className="min-h-screen bg-slate-50">
            <AppHeader />

            <main className="mx-auto max-w-[1600px] p-4 md:p-6">
                {isLoading ? (
                    <DashboardSummarySkeleton />
                ) : dashboardData ? (
                    <DashboardSummaryBar
                        summary={dashboardData.summary}
                    />
                ) : (
                    <DashboardSummaryErrorState onRetry={reloadDashboard} />
                )}

                <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
                    {/* Map */}
                    <section className="lg:col-span-6 xl:col-span-7">
                        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                            <div className="mb-4 flex items-center justify-between gap-3">
                                <h2 className="text-base font-bold text-slate-900">
                                    도시 배수 시설 위험도 지도
                                </h2>
                                {!dashboardData && (
                                    <span className="text-xs font-medium text-slate-400">
                                        데이터 불러오는 중
                                    </span>
                                )}
                            </div>
                            {dashboardData ? (
                                <RiskMap
                                    drains={dashboardData.drains}
                                    selectedId={selectedId}
                                    onSelect={setSelectedId}
                                    labelLocation={selected?.road}
                                />
                            ) : (
                                <MapLoadingState />
                            )}
                            <p className="mt-3 flex items-center gap-1.5 text-xs text-slate-400">
                                <Info className="size-3.5" />
                                지도에서 배수 시설을 클릭하면 상세 정보를 확인할
                                수 있습니다.
                            </p>
                        </div>
                    </section>

                    {/* Risk list */}
                    <section className="lg:col-span-6 xl:col-span-5 2xl:col-span-3">
                        <div className="h-full max-h-[640px] shadow-sm">
                            <DrainRiskList
                                drains={sorted}
                                selectedId={selectedId}
                                onSelect={setSelectedId}
                                status={riskListStatus}
                                realtimeStatus={riskListRealtimeStatus}
                                onRetry={reloadDashboard}
                            />
                        </div>
                    </section>

                    {/* Detail panel */}
                    <section className="lg:col-span-12 2xl:col-span-2">
                        {selected ? (
                            <div className="max-h-[640px] shadow-sm">
                                <DrainSummaryPanel drain={selected} />
                            </div>
                        ) : !isLoading ? (
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

function getRiskListStatus({
    dashboardData,
    isLoading,
}: {
    dashboardData: { sortedDrains: import("@/lib/mock-data").DrainFacility[] } | null;
    isLoading: boolean;
}): DrainRiskListStatus {
    if (isLoading) return "loading";
    if (!dashboardData) return "error";
    if (dashboardData.sortedDrains.length === 0) return "empty";
    return "success";
}

function DashboardSummaryBar({
    summary,
}: {
    summary: DashboardSummaryDto;
}) {
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
        <section className="mb-4 rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <p className="text-sm font-bold text-slate-900">
                        대시보드 현황
                    </p>
                    <p className="mt-0.5 text-xs text-slate-500">
                        API 응답 기준
                        {summary.latestUpdatedAt
                            ? ` · 최신 업데이트 ${summary.latestUpdatedAt}`
                            : ""}
                    </p>
                </div>
                <dl className="grid grid-cols-5 gap-2">
                    {items.map((item) => (
                        <div
                            key={item.label}
                            className="min-w-16 rounded-lg bg-slate-50 px-3 py-2 text-center"
                        >
                            <dt className="text-xs text-slate-500">
                                {item.label}
                            </dt>
                            <dd
                                className={`mt-0.5 text-lg font-bold ${item.className}`}
                            >
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
        <section className="mb-4 rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <div className="h-4 w-24 animate-pulse rounded bg-slate-200" />
                    <div className="mt-2 h-3 w-44 animate-pulse rounded bg-slate-100" />
                </div>
                <div className="grid grid-cols-5 gap-2">
                    {Array.from({ length: 5 }, (_, index) => (
                        <div
                            key={index}
                            className="min-w-16 rounded-lg bg-slate-50 px-3 py-2"
                        >
                            <div className="mx-auto h-3 w-10 animate-pulse rounded bg-slate-100" />
                            <div className="mx-auto mt-2 h-5 w-8 animate-pulse rounded bg-slate-200" />
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}

function DashboardSummaryErrorState({
    onRetry,
}: {
    onRetry: () => void;
}) {
    return (
        <section className="mb-4 rounded-xl border border-red-100 bg-red-50/60 px-5 py-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                    <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-white text-red-500 shadow-sm">
                        <AlertCircle className="size-5" />
                    </span>
                    <div>
                        <p className="text-sm font-bold text-red-700">
                            대시보드 현황을 불러오지 못했습니다.
                        </p>
                        <p className="mt-0.5 text-xs text-red-600/80">
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
        <div className="flex min-h-[420px] items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 text-sm font-medium text-slate-400">
            배수 시설 데이터를 불러오고 있습니다.
        </div>
    );
}
