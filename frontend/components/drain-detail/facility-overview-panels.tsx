import {
    Clipboard,
    Clock,
    Gauge,
    Globe,
    MapPin,
    ShieldCheck,
    TrendingUp,
    type LucideIcon,
} from "lucide-react";
import { StatusBadge } from "@/components/status-badge";
import { formatDateTimeForDisplay } from "@/lib/date-format";
import { STATUS_META, type DrainFacility, type RiskHistoryItem } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export function FacilityInfoCard({ drain }: { drain: DrainFacility }) {
    const meta = STATUS_META[drain.status];
    const rows: { icon: LucideIcon; label: string; node: React.ReactNode }[] = [
        {
            icon: Clipboard,
            label: "시설 ID",
            node: <span className="font-semibold text-slate-800 dark:text-slate-100">{drain.id}</span>,
        },
        {
            icon: MapPin,
            label: "주소",
            node: <span className="break-words text-slate-700 dark:text-slate-200">{drain.fullAddress}</span>,
        },
        {
            icon: ShieldCheck,
            label: "상태",
            node: <StatusBadge status={drain.status} />,
        },
        {
            icon: Globe,
            label: "막힘 정도",
            node: (
                <span className={cn("font-semibold", meta.text)}>
                    {drain.blockage == null ? "-" : `${drain.blockage}% (${meta.label})`}
                </span>
            ),
        },
        {
            icon: TrendingUp,
            label: "수위",
            node: (
                <span className={cn("font-semibold", meta.text)}>
                    {drain.waterLevelCm == null ? "-" : `${drain.waterLevelCm} cm`}
                </span>
            ),
        },
        {
            icon: Gauge,
            label: "유속",
            node: (
                <span className={cn("font-semibold", meta.text)}>
                    {drain.flowVelocityMps == null ? "-" : `${drain.flowVelocityMps} m/s`}
                </span>
            ),
        },
        {
            icon: Clock,
            label: "최근 업데이트",
            node: <span className="text-slate-700 dark:text-slate-200">{formatDateTimeForDisplay(drain.updatedAt)}</span>,
        },
    ];

    return (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5 dark:border-slate-800 dark:bg-slate-900">
            <h2 className="mb-3 text-base font-bold text-slate-900 dark:text-slate-100">
                시설 정보 및 현재 상태
            </h2>
            <dl className="divide-y divide-slate-100 dark:divide-slate-800">
                {rows.map((row) => (
                    <div
                        key={row.label}
                        className="flex items-center justify-between gap-3 py-2.5"
                    >
                        <dt className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                            <row.icon className="size-4 text-slate-400 dark:text-slate-500" />
                            {row.label}
                        </dt>
                        <dd className="max-w-[62%] text-right text-sm">{row.node}</dd>
                    </div>
                ))}
            </dl>
        </div>
    );
}

export function RiskHistoryCard({ riskHistory }: { riskHistory: RiskHistoryItem[] }) {
    return (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5 dark:border-slate-800 dark:bg-slate-900">
            <h2 className="mb-3 text-base font-bold text-slate-900 dark:text-slate-100">
                과거 위험 이력
            </h2>
            <ul className="space-y-1">
                {riskHistory.map((item) => {
                    const meta = STATUS_META[item.status];
                    return (
                        <li
                            key={item.time}
                            className="flex items-center gap-3 rounded-lg px-2 py-2.5 hover:bg-slate-50 dark:hover:bg-slate-800"
                        >
                            <span className={cn("size-2.5 shrink-0 rounded-full", meta.dot)} />
                            <span className="min-w-0 text-sm text-slate-600 dark:text-slate-300">
                                {formatDateTimeForDisplay(item.time)}
                            </span>
                            <StatusBadge status={item.status} className="ml-auto" />
                        </li>
                    );
                })}
            </ul>
        </div>
    );
}
