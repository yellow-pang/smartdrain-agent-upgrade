"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, Info, RotateCcw } from "lucide-react";
import { AppHeader } from "@/components/app-header";
import { RiskMap } from "@/components/risk-map";
import {
    DrainRiskList,
    type DrainRealtimeStatus,
    type DrainRiskListStatus,
} from "@/components/drain-risk-list";
import { DrainSummaryPanel } from "@/components/drain-summary-panel";
import { PlaceholderState } from "@/components/placeholder-state";
import { Button } from "@/components/ui/button";
import {
    loadDashboardData,
    type DashboardData,
} from "@/lib/api/drain-data";
import {
    dashboardSummaryFromDrains,
    mergeDrainStatusEventIntoFacility,
    sortFacilitiesByRisk,
} from "@/lib/api/adapters";
import type { DashboardSummaryDto, DrainStatusUpdatedEventDto } from "@/lib/api/types";
import { PLACEHOLDER_IMAGES } from "@/lib/placeholders";
import { useDrainStatusSocket } from "@/lib/websocket/drain-status-socket";

export default function DashboardPage() {
    const [dashboardData, setDashboardData] = useState<DashboardData | null>(
        null,
    );
    const [isLoading, setIsLoading] = useState(true);
    const [selectedId, setSelectedId] = useState<string | null>(null);

    const applyRealtimeEvent = useCallback(
        (event: DrainStatusUpdatedEventDto) => {
            setDashboardData((current) => {
                if (!current || current.source !== "api") return current;

                const drains = current.drains.map((drain) =>
                    mergeDrainStatusEventIntoFacility(drain, event),
                );

                return {
                    ...current,
                    drains,
                    sortedDrains: sortFacilitiesByRisk(drains),
                    summary: dashboardSummaryFromDrains(drains),
                };
            });
        },
        [],
    );

    const reloadDashboard = useCallback(() => {
        setIsLoading(true);
        loadDashboardData().then((data) => {
            setDashboardData(data);
            setSelectedId((current) => {
                if (data.source !== "api") return null;
                return current ?? data.sortedDrains[0]?.id ?? null;
            });
            setIsLoading(false);
        });
    }, []);

    useEffect(() => {
        let mounted = true;

        loadDashboardData().then((data) => {
            if (!mounted) return;
            setDashboardData(data);
            setSelectedId(
                data.source === "api" ? data.sortedDrains[0]?.id : null,
            );
            setIsLoading(false);
        });

        return () => {
            mounted = false;
        };
    }, []);

    const realtimeStatus = useDrainStatusSocket({
        enabled: dashboardData?.source === "api",
        onStatusUpdated: applyRealtimeEvent,
    });

    const selected = useMemo(() => {
        if (!dashboardData || dashboardData.source !== "api" || !selectedId) {
            return undefined;
        }
        return dashboardData.drains.find((drain) => drain.id === selectedId);
    }, [dashboardData, selectedId]);

    const sorted =
        dashboardData?.source === "api" ? dashboardData.sortedDrains : [];
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
                ) : dashboardData?.source === "api" ? (
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
                            {dashboardData?.source === "api" ? (
                                <RiskMap
                                    drains={dashboardData.drains}
                                    selectedId={selectedId}
                                    onSelect={setSelectedId}
                                    labelLocation={selected?.road}
                                />
                            ) : dashboardData?.source === "mock" ? (
                                <PlaceholderState
                                    image={PLACEHOLDER_IMAGES.map}
                                    title="지도 API 연결 대기"
                                    description="실제 백엔드 데이터가 도착하면 지도 마커가 표시됩니다."
                                    statusLabel="mock fallback"
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
                        ) : dashboardData?.source === "mock" ? (
                            <PlaceholderState
                                image={PLACEHOLDER_IMAGES.facility}
                                title="상세 정보 연결 대기"
                                description="목록 API가 연결되면 선택한 시설의 상세 정보가 표시됩니다."
                                statusLabel="mock fallback"
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
    dashboardData: DashboardData | null;
    isLoading: boolean;
}): DrainRiskListStatus {
    if (isLoading) return "loading";
    if (!dashboardData || dashboardData.source === "mock") return "error";
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
