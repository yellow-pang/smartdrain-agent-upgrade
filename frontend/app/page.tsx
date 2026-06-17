"use client";

import { useMemo, useState } from "react";
import { Info } from "lucide-react";
import { AppHeader } from "@/components/app-header";
import { RiskMap } from "@/components/risk-map";
import { DrainRiskList } from "@/components/drain-risk-list";
import { DrainSummaryPanel } from "@/components/drain-summary-panel";
import { DRAINS, getDrainById, sortByRisk } from "@/lib/mock-data";

export default function DashboardPage() {
    const sorted = useMemo(() => sortByRisk(DRAINS), []);
    const [selectedId, setSelectedId] = useState<string>(
        sorted[0]?.id ?? "DR-004",
    );
    const selected = getDrainById(selectedId);

    return (
        <div className="min-h-screen bg-slate-50">
            <AppHeader />

            <main className="mx-auto max-w-[1600px] p-4 md:p-6">
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
                    {/* Map */}
                    <section className="lg:col-span-6 xl:col-span-7">
                        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                            <h2 className="mb-4 text-base font-bold text-slate-900">
                                도시 배수 시설 위험도 지도
                            </h2>
                            <RiskMap
                                drains={DRAINS}
                                selectedId={selectedId}
                                onSelect={setSelectedId}
                                labelLocation={selected?.road}
                            />
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
