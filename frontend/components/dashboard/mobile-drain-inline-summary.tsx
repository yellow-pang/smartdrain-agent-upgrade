import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { formatDateTimeForDisplay } from "@/lib/date-format";
import { getDrainDetailHref } from "@/lib/drain-route";
import type { DrainFacility } from "@/lib/mock-data";

export function MobileDrainInlineSummary({ drain }: { drain: DrainFacility }) {
    return (
        <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    선택 시설 요약
                </p>
                <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                        <p className="text-xs text-slate-500 dark:text-slate-400">시설명</p>
                        <p className="overflow-hidden text-sm font-semibold text-slate-900 [display:-webkit-box] [-webkit-box-orient:vertical] [-webkit-line-clamp:1] dark:text-slate-100">
                            {drain.road}
                        </p>
                    </div>
                    <StatusBadge status={drain.status} className="shrink-0" />
                </div>
                <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
                    <Metric label="막힘" value={drain.blockage == null ? "-" : `${drain.blockage}%`} />
                    <Metric
                        label="수위"
                        value={drain.waterLevelCm == null ? "-" : `${drain.waterLevelCm} cm`}
                    />
                    <Metric
                        label="유속"
                        value={drain.flowVelocityMps == null ? "-" : `${drain.flowVelocityMps} m/s`}
                    />
                </div>
                <p className="mt-2 text-[11px] text-slate-500 dark:text-slate-400">
                    최근 업데이트 {formatDateTimeForDisplay(drain.updatedAt)}
                </p>
                <Button
                    nativeButton={false}
                    className="mt-2 h-9 w-full bg-cyan-700 text-white hover:bg-cyan-800"
                    render={
                        <Link href={getDrainDetailHref(drain.id)}>
                            상세 정보 페이지로 이동
                            <ChevronRight className="size-4" />
                        </Link>
                    }
                />
            </div>
        </section>
    );
}

function Metric({ label, value }: { label: string; value: string }) {
    return (
        <div className="rounded-md bg-slate-50 px-2.5 py-2 dark:bg-slate-800/80">
            <p className="text-slate-500 dark:text-slate-400">{label}</p>
            <p className="mt-0.5 font-semibold text-slate-800 dark:text-slate-100">{value}</p>
        </div>
    );
}
