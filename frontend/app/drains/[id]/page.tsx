"use client";

import Link from "next/link";
import { use, useEffect, useMemo, useState } from "react";
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
import { PlaceholderState } from "@/components/placeholder-state";
import { STATUS_META, type RiskStatus } from "@/lib/mock-data";
import {
    loadDrainDetailData,
    type DrainDetailData,
} from "@/lib/api/drain-data";
import { cn } from "@/lib/utils";
import type { AnalysisResultDto, YoloStatus } from "@/lib/api/types";
import { PLACEHOLDER_IMAGES } from "@/lib/placeholders";

export default function DrainDetailPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = use(params);
    const [detailData, setDetailData] = useState<DrainDetailData | null>();

    useEffect(() => {
        let mounted = true;

        loadDrainDetailData(id).then((data) => {
            if (!mounted) return;
            setDetailData(data);
        });

        return () => {
            mounted = false;
        };
    }, [id]);

    const drain = detailData?.drain;
    const meta = drain ? STATUS_META[drain.status] : undefined;
    const sensorSummary = useMemo(() => {
        if (!detailData) return undefined;
        return getSensorSummary(detailData.sensorHistory);
    }, [detailData]);

    if (detailData === null) notFound();

    if (!drain || !meta || !sensorSummary) {
        return (
            <div className="min-h-screen bg-slate-50">
                <AppHeader />
                <main className="mx-auto max-w-[1600px] p-4 md:p-6">
                    <DetailLoadingState />
                </main>
            </div>
        );
    }

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
                    <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-500">
                        {detailData.source === "api"
                            ? "API 데이터"
                            : "mock fallback"}
                    </span>
                </div>

                <div className="mt-5 grid grid-cols-1 gap-4 xl:grid-cols-12">
                    {/* Left column */}
                    <div className="flex flex-col gap-4 xl:col-span-4">
                        <CctvSnapshotCard
                            snapshots={getSnapshots(detailData)}
                            locationName={drain.road}
                        />
                        <LocationMapCard
                            drain={drain}
                            fullAddress={drain.fullAddress}
                            road={drain.road}
                            source={detailData.source}
                        />
                    </div>

                    {/* Middle column */}
                    <div className="flex flex-col gap-4 xl:col-span-5">
                        <SensorTrendChart
                            points={detailData.sensorHistory}
                            summary={sensorSummary}
                            isFallback={detailData.source === "mock"}
                        />
                        <CurrentRiskCard drain={drain} meta={meta} />
                        <AnalysisResultCard analysis={detailData.analysis} />
                    </div>

                    {/* Right column */}
                    <div className="flex flex-col gap-4 xl:col-span-3">
                        <FacilityInfoCard drain={drain} meta={meta} />
                        <RiskHistoryCard riskHistory={detailData.riskHistory} />
                    </div>
                </div>
            </main>
        </div>
    );
}

function LocationMapCard({
    drain,
    fullAddress,
    road,
    source,
}: {
    drain: DrainDetailData["drain"];
    fullAddress: string;
    road: string;
    source: DrainDetailData["source"];
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
                {source === "api" ? (
                    <RiskMap
                        drains={[{ ...drain, x: 50, y: 48 }]}
                        selectedId={drain.id}
                        labelLocation={road}
                    />
                ) : (
                    <PlaceholderState
                        image={PLACEHOLDER_IMAGES.map}
                        title="위치 지도 연결 대기"
                        description="실제 위치 데이터가 도착하면 지도 영역이 표시됩니다."
                        statusLabel="mock fallback"
                        className="h-full min-h-0"
                    />
                )}
            </div>
            <p className="mt-3 flex items-center gap-1.5 text-xs text-slate-500">
                <MapPin className="size-3.5 text-slate-400" />
                {fullAddress}
            </p>
        </div>
    );
}

function CurrentRiskCard({
    drain,
    meta,
}: {
    drain: DrainDetailData["drain"];
    meta: (typeof STATUS_META)[RiskStatus];
}) {
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
                                {meta.label}
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
                                {meta.label}
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
                            {meta.label}
                        </span>
                    </div>
                </RiskTile>
                <RiskTile icon={Clock} label="최근 업데이트">
                    <span className="text-sm font-semibold text-slate-700">
                        {drain.updatedAt}
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
    drain: DrainDetailData["drain"];
    meta: (typeof STATUS_META)[RiskStatus];
}) {
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
            node: <span className="text-slate-700">{drain.fullAddress}</span>,
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
                    {drain.blockage}% ({meta.label})
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
            node: <span className="text-slate-700">{drain.updatedAt}</span>,
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

function AnalysisResultCard({
    analysis,
}: {
    analysis?: AnalysisResultDto;
}) {
    const yolo = analysis?.yoloResult;
    const xgboost = analysis?.xgboostResult;
    const riskMeta = xgboost ? STATUS_META[xgboost.riskLevel] : undefined;

    return (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 text-base font-bold text-slate-900">
                YOLO / XGBoost 분석 결과
            </h2>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <AnalysisMetric
                    label="YOLO 막힘 상태"
                    value={yolo ? getYoloStatusLabel(yolo.yoloStatus) : "없음"}
                    tone={yolo ? "text-slate-900" : "text-slate-400"}
                />
                <AnalysisMetric
                    label="YOLO 신뢰도"
                    value={
                        yolo
                            ? `${Math.round(yolo.confidenceScore * 100)}%`
                            : "없음"
                    }
                    tone={yolo ? "text-cyan-700" : "text-slate-400"}
                />
                <AnalysisMetric
                    label="XGBoost 위험 점수"
                    value={
                        xgboost
                            ? `${Math.round(xgboost.riskScore * 100)}점`
                            : "없음"
                    }
                    tone={riskMeta?.text ?? "text-slate-400"}
                />
                <AnalysisMetric
                    label="최종 판단"
                    value={xgboost?.finalDecision ?? "분석 결과 없음"}
                    tone={riskMeta?.text ?? "text-slate-400"}
                />
            </div>
            {(yolo?.analyzedAt || xgboost?.predictedAt) && (
                <p className="mt-3 text-xs text-slate-400">
                    YOLO {yolo?.analyzedAt ?? "-"} · XGBoost{" "}
                    {xgboost?.predictedAt ?? "-"}
                </p>
            )}
        </div>
    );
}

function AnalysisMetric({
    label,
    value,
    tone,
}: {
    label: string;
    value: string;
    tone: string;
}) {
    return (
        <div className="rounded-lg border border-slate-100 bg-slate-50/60 px-3 py-3">
            <p className="text-xs text-slate-500">{label}</p>
            <p className={cn("mt-1 text-sm font-bold", tone)}>{value}</p>
        </div>
    );
}

function RiskHistoryCard({
    riskHistory,
}: {
    riskHistory: DrainDetailData["riskHistory"];
}) {
    return (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-base font-bold text-slate-900">
                과거 위험 이력{" "}
                <span className="text-sm font-normal text-slate-400">
                    (최근 7일)
                </span>
            </h2>
            <ul className="space-y-1">
                {riskHistory.map((item) => {
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

function DetailLoadingState() {
    return (
        <div className="rounded-xl border border-dashed border-slate-200 bg-white px-5 py-10 text-center text-sm font-medium text-slate-400">
            배수 시설 상세 데이터를 불러오고 있습니다.
        </div>
    );
}

function getSensorSummary(points: DrainDetailData["sensorHistory"]) {
    const fallback = {
        currentLevel: 0,
        currentFlow: 0,
        maxLevel: 0,
        maxLevelTime: "-",
        maxFlow: 0,
        maxFlowTime: "-",
    };
    if (points.length === 0) return fallback;

    const latest = points[points.length - 1];
    const maxLevel = points.reduce((max, point) =>
        point.level > max.level ? point : max,
    );
    const maxFlow = points.reduce((max, point) =>
        point.flow > max.flow ? point : max,
    );

    return {
        currentLevel: latest.level,
        currentFlow: latest.flow,
        maxLevel: maxLevel.level,
        maxLevelTime: maxLevel.time,
        maxFlow: maxFlow.flow,
        maxFlowTime: maxFlow.time,
    };
}

function getSnapshots(detailData: DrainDetailData) {
    const imageUrl =
        detailData.analysis?.yoloResult?.imageUrl ??
        detailData.detail.imageUrl ??
        PLACEHOLDER_IMAGES.cctv;
    const capturedAt =
        detailData.analysis?.yoloResult?.analyzedAt ??
        detailData.drain.updatedAt;

    return [{ imageUrl, capturedAt }];
}

function getYoloStatusLabel(status: YoloStatus) {
    const labels: Record<YoloStatus, string> = {
        clear: "막힘 없음",
        partially_blocked: "일부 막힘",
        blocked: "심한 막힘",
        unknown: "판단불가",
    };
    return labels[status];
}
