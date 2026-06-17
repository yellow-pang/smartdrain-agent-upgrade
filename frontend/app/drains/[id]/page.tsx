"use client";

import Link from "next/link";
import { use } from "react";
import { notFound } from "next/navigation";
import {
    AlertTriangle,
    ArrowLeft,
    Clipboard,
    Clock,
    Gauge,
    Globe,
    MapPin,
    ShieldCheck,
    TrendingUp,
    Waves,
} from "lucide-react";
import { AppHeader } from "@/components/app-header";
import { CctvSnapshotCard } from "@/components/cctv-snapshot-card";
import { SensorTrendChart } from "@/components/sensor-trend-chart";
import { StatusBadge } from "@/components/status-badge";
import { MetricProgress } from "@/components/metric-progress";
import { RiskMap } from "@/components/risk-map";
import {
    getDrainById,
    RISK_HISTORY,
    STATUS_META,
    type RiskStatus,
} from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export default function DrainDetailPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = use(params);
    const drain = getDrainById(id);
    if (!drain) notFound();

    const meta = STATUS_META[drain.status];

    return (
        <div className="min-h-screen bg-slate-50">
            <AppHeader />

            <main className="mx-auto max-w-[1600px] p-4 md:p-6">
                <Link
                    href="/"
                    className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-700"
                >
                    <ArrowLeft className="size-4" />
                    대시보드로 돌아가기
                </Link>

                <div className="mt-2 flex flex-wrap items-baseline gap-3">
                    <h1 className="text-2xl font-bold tracking-tight text-slate-900">
                        하수구 상세 정보
                    </h1>
                    <span className="text-sm font-medium text-slate-500">
                        {drain.id} · {drain.road}
                    </span>
                </div>

                <div className="mt-5 grid grid-cols-1 gap-4 xl:grid-cols-12">
                    {/* Left column */}
                    <div className="flex flex-col gap-4 xl:col-span-4">
                        <CctvSnapshotCard />
                        <LocationMapCard
                            fullAddress={drain.fullAddress}
                            road={drain.road}
                            drainId={drain.id}
                        />
                    </div>

                    {/* Middle column */}
                    <div className="flex flex-col gap-4 xl:col-span-5">
                        <SensorTrendChart />
                        <CurrentRiskCard drain={drain} meta={meta} />
                    </div>

                    {/* Right column */}
                    <div className="flex flex-col gap-4 xl:col-span-3">
                        <FacilityInfoCard drain={drain} meta={meta} />
                        <RiskHistoryCard />
                    </div>
                </div>
            </main>
        </div>
    );
}

function LocationMapCard({
    fullAddress,
    road,
    drainId,
}: {
    fullAddress: string;
    road: string;
    drainId: string;
}) {
    return (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-base font-bold text-slate-900">
                위치 지도{" "}
                <span className="text-sm font-normal text-slate-400">
                    (고정)
                </span>
            </h2>
            <div className="h-[260px]">
                <RiskMap
                    drains={[{ ...drainOnly(drainId), x: 50, y: 48 }]}
                    selectedId={drainId}
                    labelLocation={road}
                />
            </div>
            <p className="mt-3 flex items-center gap-1.5 text-xs text-slate-500">
                <MapPin className="size-3.5 text-slate-400" />
                {fullAddress}
            </p>
        </div>
    );
}

// helper to render only the selected drain on the location map
function drainOnly(id: string) {
    return getDrainById(id)!;
}

function CurrentRiskCard({
    drain,
    meta,
}: {
    drain: ReturnType<typeof getDrainById> & {};
    meta: (typeof STATUS_META)[RiskStatus];
}) {
    if (!drain) return null;
    return (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 text-base font-bold text-slate-900">
                현재 위험 상태
            </h2>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <RiskTile icon={ShieldCheck} label="상태">
                    <StatusBadge status={drain.status} />
                </RiskTile>
                <RiskTile icon={Globe} label="막힘 정도">
                    <div className="w-full">
                        <div className="flex items-center justify-between">
                            <span className="text-lg font-bold text-slate-900">
                                {drain.blockage}%
                            </span>
                            <span
                                className={cn(
                                    "text-xs font-semibold",
                                    meta.text,
                                )}
                            >
                                높음
                            </span>
                        </div>
                        <MetricProgress
                            value={drain.blockage}
                            barClass={meta.bar}
                            className="mt-1.5"
                        />
                    </div>
                </RiskTile>
                <RiskTile icon={Waves} label="수위">
                    <div className="w-full">
                        <div className="flex items-center justify-between">
                            <span className="text-lg font-bold text-slate-900">
                                {drain.waterLevelPct}%
                            </span>
                            <span
                                className={cn(
                                    "text-xs font-semibold",
                                    meta.text,
                                )}
                            >
                                높음
                            </span>
                        </div>
                        <MetricProgress
                            value={drain.waterLevelPct}
                            barClass={meta.bar}
                            className="mt-1.5"
                        />
                    </div>
                </RiskTile>
                <RiskTile icon={Gauge} label="유량">
                    <div className="flex items-baseline gap-2">
                        <span className="text-lg font-bold text-slate-900">
                            {drain.flow} m³/min
                        </span>
                        <span
                            className={cn("text-xs font-semibold", meta.text)}
                        >
                            높음
                        </span>
                    </div>
                </RiskTile>
                <RiskTile icon={Clock} label="최근 업데이트">
                    <span className="text-sm font-semibold text-slate-700">
                        2024-05-23 14:30:00
                    </span>
                </RiskTile>
                <RiskTile icon={AlertTriangle} label="판정 결과">
                    <span className={cn("text-base font-bold", meta.text)}>
                        {drain.judgement}
                    </span>
                </RiskTile>
            </div>
        </div>
    );
}

function RiskTile({
    icon: Icon,
    label,
    children,
}: {
    icon: React.ElementType;
    label: string;
    children: React.ReactNode;
}) {
    return (
        <div className="flex items-center gap-3 rounded-lg border border-slate-100 bg-slate-50/60 px-3 py-3">
            <span className="flex size-8 shrink-0 items-center justify-center rounded-md bg-white text-slate-400 shadow-sm">
                <Icon className="size-4" />
            </span>
            <div className="min-w-0 flex-1">
                <p className="text-xs text-slate-500">{label}</p>
                <div className="mt-0.5">{children}</div>
            </div>
        </div>
    );
}

function FacilityInfoCard({
    drain,
    meta,
}: {
    drain: ReturnType<typeof getDrainById> & {};
    meta: (typeof STATUS_META)[RiskStatus];
}) {
    if (!drain) return null;
    const rows: {
        icon: React.ElementType;
        label: string;
        node: React.ReactNode;
    }[] = [
        {
            icon: Clipboard,
            label: "시설 ID",
            node: (
                <span className="font-semibold text-slate-800">{drain.id}</span>
            ),
        },
        {
            icon: MapPin,
            label: "주소",
            node: (
                <span className="text-slate-700">
                    서울시 강남구 테헤란로 123
                </span>
            ),
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
                    {drain.blockage}% (높음)
                </span>
            ),
        },
        {
            icon: TrendingUp,
            label: "수위",
            node: (
                <span className={cn("font-semibold", meta.text)}>
                    {drain.waterLevelM} m
                </span>
            ),
        },
        {
            icon: Gauge,
            label: "유량",
            node: (
                <span className={cn("font-semibold", meta.text)}>
                    {drain.flow} m³/min
                </span>
            ),
        },
        {
            icon: Clock,
            label: "최근 업데이트",
            node: <span className="text-slate-700">2024-05-23 14:30:00</span>,
        },
    ];
    return (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-base font-bold text-slate-900">
                시설 정보 및 현재 상태
            </h2>
            <dl className="divide-y divide-slate-100">
                {rows.map((r) => (
                    <div
                        key={r.label}
                        className="flex items-center justify-between gap-3 py-2.5"
                    >
                        <dt className="flex items-center gap-2 text-sm text-slate-500">
                            <r.icon className="size-4 text-slate-400" />
                            {r.label}
                        </dt>
                        <dd className="text-right text-sm">{r.node}</dd>
                    </div>
                ))}
            </dl>
        </div>
    );
}

function RiskHistoryCard() {
    return (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-base font-bold text-slate-900">
                과거 위험 이력{" "}
                <span className="text-sm font-normal text-slate-400">
                    (최근 7일)
                </span>
            </h2>
            <ul className="space-y-1">
                {RISK_HISTORY.map((item) => {
                    const meta = STATUS_META[item.status];
                    return (
                        <li
                            key={item.time}
                            className="flex items-center gap-3 rounded-lg px-2 py-2.5 hover:bg-slate-50"
                        >
                            <span
                                className={cn(
                                    "size-2.5 shrink-0 rounded-full",
                                    meta.dot,
                                )}
                            />
                            <span className="text-sm text-slate-600">
                                {item.time}
                            </span>
                            <StatusBadge
                                status={item.status}
                                className="ml-auto"
                            />
                            <span className="w-10 shrink-0 text-right text-sm font-semibold text-slate-700">
                                {item.score}점
                            </span>
                        </li>
                    );
                })}
            </ul>
        </div>
    );
}
