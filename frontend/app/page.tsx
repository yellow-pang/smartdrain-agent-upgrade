"use client";

import { useEffect, useMemo, useState } from "react";
import { Info } from "lucide-react";
import { AppHeader } from "@/components/app-header";
import { RiskMap } from "@/components/risk-map";
import { DrainRiskList } from "@/components/drain-risk-list";
import { DrainSummaryPanel } from "@/components/drain-summary-panel";
import {
    loadDashboardData,
    type DashboardData,
} from "@/lib/api/drain-data";
import type { DashboardSummaryDto } from "@/lib/api/types";

export default function DashboardPage() {
    const [dashboardData, setDashboardData] = useState<DashboardData | null>(
        null,
    );
    const [selectedId, setSelectedId] = useState<string | null>(null);

    useEffect(() => {
        let mounted = true;

        loadDashboardData().then((data) => {
            if (!mounted) return;
            setDashboardData(data);
            setSelectedId((current) => current ?? data.sortedDrains[0]?.id);
        });

        return () => {
            mounted = false;
        };
    }, []);

    const selected = useMemo(() => {
        if (!dashboardData || !selectedId) return undefined;
        return dashboardData.drains.find((drain) => drain.id === selectedId);
    }, [dashboardData, selectedId]);

    const sorted = dashboardData?.sortedDrains ?? [];

    return (
        <div className="min-h-screen bg-slate-50">
            <AppHeader />

            <main className="mx-auto max-w-[1600px] p-4 md:p-6">
                {dashboardData && (
                    <DashboardSummaryBar
                        summary={dashboardData.summary}
                        source={dashboardData.source}
                    />
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
                            />
                        </div>
                    </section>

                    {/* Detail panel */}
                    <section className="lg:col-span-12 2xl:col-span-2">
                        {selected && (
                            <div className="max-h-[640px] shadow-sm">
                                <DrainSummaryPanel drain={selected} />
                            </div>
                        )}
                    </section>
                </div>
            </main>
        </div>
    );
}

function DashboardSummaryBar({
    summary,
    source,
}: {
    summary: DashboardSummaryDto;
    source: "api" | "mock";
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
                        {source === "api"
                            ? "API 응답 기준"
                            : "API 명세형 mock fallback 기준"}
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

function MapLoadingState() {
    return (
        <div className="flex min-h-[420px] items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 text-sm font-medium text-slate-400">
            배수 시설 데이터를 불러오고 있습니다.
        </div>
    );
}
