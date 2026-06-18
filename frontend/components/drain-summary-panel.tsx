"use client";

import Link from "next/link";
import {
    ChevronRight,
    Clock,
    Gauge,
    MapPin,
    Maximize2,
    ShieldCheck,
    TrendingUp,
    Waves,
    X,
} from "lucide-react";
import { STATUS_META, type DrainFacility } from "@/lib/mock-data";
import { StatusBadge } from "@/components/status-badge";
import { MetricProgress } from "@/components/metric-progress";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function DrainSummaryPanel({
    drain,
    onClose,
    imageUrl = "/cctv-drain.png",
}: {
    drain: DrainFacility;
    onClose?: () => void;
    imageUrl?: string;
}) {
    const meta = STATUS_META[drain.status];
    return (
        <div className="flex h-full flex-col rounded-xl border border-slate-200 bg-white">
            <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
                <h2 className="text-base font-bold text-slate-900">
                    상세 정보
                </h2>
                {onClose && (
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-slate-600"
                        aria-label="패널 닫기"
                    >
                        <X className="size-4" />
                    </button>
                )}
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-4">
                <p className="text-sm font-semibold text-slate-900">
                    {drain.road}{" "}
                    <span className="font-normal text-slate-500">
                        (빗물받이)
                    </span>
                </p>

                {/* CCTV snapshot */}
                <div className="relative mt-3 aspect-[4/3] overflow-hidden rounded-lg border border-slate-200 bg-slate-100">
                    <img
                        src={imageUrl}
                        alt={`${drain.road} 빗물받이 CCTV 스냅샷`}
                        className="size-full object-cover grayscale"
                    />
                    <span className="absolute right-2 top-2 flex size-7 items-center justify-center rounded-md bg-black/45 text-white">
                        <Maximize2 className="size-3.5" />
                    </span>
                </div>

                {/* Info rows */}
                <dl className="mt-4 space-y-3">
                    <InfoRow
                        icon={MapPin}
                        label="주소"
                        value={drain.fullAddress}
                    />
                    <InfoRow icon={ShieldCheck} label="상태">
                        <StatusBadge status={drain.status} />
                    </InfoRow>
                    <InfoRow icon={Waves} label="막힘 정도">
                        <span className={cn("font-semibold", meta.text)}>
                            {drain.blockage}% (높음)
                        </span>
                    </InfoRow>
                    <InfoRow icon={TrendingUp} label="수위">
                        <span className={cn("font-semibold", meta.text)}>
                            {drain.waterLevelPct}% (높음)
                        </span>
                    </InfoRow>
                    <InfoRow icon={Gauge} label="유량">
                        <span className={cn("font-semibold", meta.text)}>
                            {drain.flow} m³/min (높음)
                        </span>
                    </InfoRow>
                    <InfoRow
                        icon={Clock}
                        label="최근 업데이트"
                        value={drain.updatedAt}
                    />
                </dl>

                {/* blockage bar */}
                <div className="mt-4 rounded-lg border border-slate-100 bg-slate-50 p-3">
                    <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-500">판정 결과</span>
                        <span className={cn("font-bold", meta.text)}>
                            {drain.judgement}
                        </span>
                    </div>
                    <MetricProgress
                        value={drain.blockage}
                        barClass={meta.bar}
                        className="mt-2"
                        trackClass="bg-white"
                    />
                </div>
            </div>

            <div className="border-t border-slate-100 p-4">
                <Button
                    nativeButton={false}
                    className="w-full bg-cyan-700 text-white hover:bg-cyan-800"
                    render={
                        <Link href={`/drains/${drain.id}`}>
                            상세 정보 페이지로 이동
                            <ChevronRight className="size-4" />
                        </Link>
                    }
                />
            </div>
        </div>
    );
}

function InfoRow({
    icon: Icon,
    label,
    value,
    children,
}: {
    icon: React.ElementType;
    label: string;
    value?: string;
    children?: React.ReactNode;
}) {
    return (
        <div className="flex items-center justify-between gap-3">
            <dt className="flex items-center gap-2 text-sm text-slate-500">
                <Icon className="size-4 text-slate-400" />
                {label}
            </dt>
            <dd className="text-right text-sm text-slate-800">
                {children ?? <span className="font-medium">{value}</span>}
            </dd>
        </div>
    );
}
