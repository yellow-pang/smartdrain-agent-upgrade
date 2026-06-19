"use client";

import Link from "next/link";
import { use, useCallback, useEffect, useMemo, useState } from "react";
import { notFound } from "next/navigation";
import {
    AlertTriangle,
    ArrowLeft,
    Brain,
    Clipboard,
    Clock,
    Eye,
    Gauge,
    Globe,
    Images,
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
import { mergeDrainStatusEventIntoFacility } from "@/lib/api/adapters";
import { cn } from "@/lib/utils";
import { PLACEHOLDER_IMAGES } from "@/lib/placeholders";
import { useDrainStatusSocket } from "@/lib/websocket/drain-status-socket";
import type {
    DrainStatusUpdatedEventDto,
    XgboostResultDto,
    XgboostResultUpdatedEventDto,
    YoloResultDto,
    YoloResultUpdatedEventDto,
} from "@/lib/api/types";

export default function DrainDetailPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = use(params);
    const [detailData, setDetailData] = useState<DrainDetailData | null>();

    const applyRealtimeEvent = useCallback(
        (event: DrainStatusUpdatedEventDto) => {
            setDetailData((current) => {
                if (
                    !current ||
                    current.source !== "api" ||
                    current.drain.id !== event.payload.drainId
                ) {
                    return current;
                }

                return {
                    ...current,
                    drain: mergeDrainStatusEventIntoFacility(
                        current.drain,
                        event,
                    ),
                };
            });
        },
        [],
    );

    const applyYoloEvent = useCallback((event: YoloResultUpdatedEventDto) => {
        setDetailData((current) => {
            if (
                !current ||
                current.source !== "api" ||
                current.drain.id !== event.payload.drainId
            ) {
                return current;
            }

            const yoloResult = yoloEventToDto(event);
            const yoloResults = upsertYoloResult(
                current.analysisHistory?.yoloResults ?? [],
                yoloResult,
            );

            return {
                ...current,
                drain: {
                    ...current.drain,
                    blockage:
                        yoloResult.obstructionRatio == null
                            ? current.drain.blockage
                            : ratioToPercent(yoloResult.obstructionRatio),
                    updatedAt: event.payload.updatedAt,
                },
                analysis: {
                    ...current.analysis,
                    yoloResult,
                    updatedAt: event.payload.updatedAt,
                },
                analysisHistory: {
                    drainId: event.payload.drainId,
                    yoloResults,
                    xgboostResults:
                        current.analysisHistory?.xgboostResults ?? [],
                },
            };
        });
    }, []);

    const applyXgboostEvent = useCallback(
        (event: XgboostResultUpdatedEventDto) => {
            setDetailData((current) => {
                if (
                    !current ||
                    current.source !== "api" ||
                    current.drain.id !== event.payload.drainId
                ) {
                    return current;
                }

                const xgboostResult = xgboostEventToDto(event);
                const xgboostResults = upsertXgboostResult(
                    current.analysisHistory?.xgboostResults ?? [],
                    xgboostResult,
                );

                return {
                    ...current,
                    drain: {
                        ...current.drain,
                        status: event.payload.riskLevel,
                        judgement:
                            event.payload.finalDecision ??
                            current.drain.judgement,
                        updatedAt: event.payload.updatedAt,
                    },
                    analysis: {
                        ...current.analysis,
                        xgboostResult,
                        updatedAt: event.payload.updatedAt,
                    },
                    analysisHistory: {
                        drainId: event.payload.drainId,
                        yoloResults: current.analysisHistory?.yoloResults ?? [],
                        xgboostResults,
                    },
                    riskHistory: [
                        {
                            time: event.payload.evaluatedAt,
                            status: event.payload.riskLevel,
                            score: riskScoreToPoint(event.payload.riskScore),
                        },
                        ...current.riskHistory,
                    ].slice(0, 10),
                };
            });
        },
        [],
    );

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

    useDrainStatusSocket({
        enabled: detailData?.source === "api",
        onStatusUpdated: applyRealtimeEvent,
        onYoloUpdated: applyYoloEvent,
        onXgboostUpdated: applyXgboostEvent,
    });

    const drain = detailData?.drain;
    const meta = drain ? STATUS_META[drain.status] : undefined;
    const sensorSummary = useMemo(() => {
        if (!detailData) return undefined;
        return getSensorSummary(detailData.sensorHistory);
    }, [detailData]);

    if (detailData === null) notFound();

    if (detailData?.source === "mock") {
        return <DrainDetailFallbackPage drainId={id} />;
    }

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

                <AnalysisSummaryCard detailData={detailData} meta={meta} />

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
                        />
                        <AiAnalysisTabs detailData={detailData} meta={meta} />
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

function DrainDetailFallbackPage({ drainId }: { drainId: string }) {
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
                        {drainId}
                    </span>
                    <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-500">
                        mock fallback
                    </span>
                </div>

                <div className="mt-5 grid grid-cols-1 gap-4 xl:grid-cols-12">
                    <div className="flex flex-col gap-4 xl:col-span-4">
                        <CctvSnapshotCard
                            snapshots={[]}
                            locationName="API 연결 대기 시설"
                        />
                        <PlaceholderState
                            image={PLACEHOLDER_IMAGES.map}
                            title="위치 지도 연결 대기"
                            description="상세 API가 연결되면 실제 주소와 위치 지도가 표시됩니다."
                            statusLabel="mock fallback"
                            className="min-h-[340px]"
                        />
                    </div>

                    <div className="flex flex-col gap-4 xl:col-span-5">
                        <SensorTrendChart
                            points={[]}
                            summary={getFallbackSensorSummary()}
                            isFallback
                        />
                        <DetailUnavailableCard
                            title="현재 위험 상태 연결 대기"
                            description="상세 API가 연결되면 상태, 막힘 정도, 수위, 유량이 표시됩니다."
                        />
                    </div>

                    <div className="flex flex-col gap-4 xl:col-span-3">
                        <PlaceholderState
                            image={PLACEHOLDER_IMAGES.facility}
                            title="시설 정보 연결 대기"
                            description="실제 상세 데이터가 도착하면 시설 정보 row가 표시됩니다."
                            statusLabel="mock fallback"
                            className="min-h-[320px]"
                        />
                        <RiskHistoryUnavailableCard />
                    </div>
                </div>
            </main>
        </div>
    );
}

function AnalysisSummaryCard({
    detailData,
    meta,
}: {
    detailData: DrainDetailData;
    meta: (typeof STATUS_META)[RiskStatus];
}) {
    const drain = detailData.drain;
    const yoloResult = getLatestYoloResult(detailData);
    const xgboostResult = getLatestXgboostResult(detailData);
    const riskScore = riskScoreToPoint(xgboostResult?.riskScore);
    const obstructionPercent =
        yoloResult?.obstructionRatio == null
            ? drain.blockage
            : ratioToPercent(yoloResult.obstructionRatio);

    return (
        <section className="mt-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                        Detail dashboard
                    </p>
                    <h2 className="mt-1 text-lg font-bold text-slate-900">
                        현재 분석 요약
                    </h2>
                </div>
                <StatusBadge status={drain.status} />
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
                <SummaryMetricTile
                    icon={Globe}
                    label="막힘 정도"
                    value={`${obstructionPercent}%`}
                    metaText={meta.text}
                    progress={obstructionPercent}
                    barClass={meta.bar}
                />
                <SummaryMetricTile
                    icon={Waves}
                    label="수위"
                    value={`${drain.waterLevelPct}%`}
                    subValue={`${drain.waterLevelM} m`}
                    metaText={meta.text}
                    progress={drain.waterLevelPct}
                    barClass={meta.bar}
                />
                <SummaryMetricTile
                    icon={Gauge}
                    label="유속"
                    value={`${drain.flow} m/s`}
                    metaText={meta.text}
                />
                <SummaryMetricTile
                    icon={Brain}
                    label="위험 점수"
                    value={`${riskScore}점`}
                    metaText={meta.text}
                    progress={riskScore}
                    barClass={meta.bar}
                />
                <div className="rounded-lg border border-slate-100 bg-slate-50/70 p-3">
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                        <AlertTriangle className="size-4 text-slate-400" />
                        최종 판단
                    </div>
                    <p className={cn("mt-2 text-sm font-bold", meta.text)}>
                        {xgboostResult?.finalDecision ?? drain.judgement}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                        {formatDisplayTime(
                            xgboostResult?.evaluatedAt ??
                                xgboostResult?.predictedAt ??
                                drain.updatedAt,
                        )}
                    </p>
                </div>
            </div>
        </section>
    );
}

function SummaryMetricTile({
    icon: Icon,
    label,
    value,
    subValue,
    metaText,
    progress,
    barClass,
}: {
    icon: React.ElementType;
    label: string;
    value: string;
    subValue?: string;
    metaText: string;
    progress?: number;
    barClass?: string;
}) {
    return (
        <div className="rounded-lg border border-slate-100 bg-slate-50/70 p-3">
            <div className="flex items-center gap-2 text-xs text-slate-500">
                <Icon className="size-4 text-slate-400" />
                {label}
            </div>
            <div className="mt-2 flex items-baseline gap-2">
                <span className={cn("text-xl font-bold", metaText)}>
                    {value}
                </span>
                {subValue ? (
                    <span className="text-xs font-semibold text-slate-400">
                        {subValue}
                    </span>
                ) : null}
            </div>
            {progress != null && barClass ? (
                <MetricProgress
                    value={progress}
                    barClass={barClass}
                    className="mt-3"
                />
            ) : null}
        </div>
    );
}

function AiAnalysisTabs({
    detailData,
    meta,
}: {
    detailData: DrainDetailData;
    meta: (typeof STATUS_META)[RiskStatus];
}) {
    const [activeTab, setActiveTab] = useState<
        "summary" | "yolo" | "xgboost" | "history"
    >("summary");
    const tabs = [
        { id: "summary", label: "요약", icon: ShieldCheck },
        { id: "yolo", label: "YOLO", icon: Eye },
        { id: "xgboost", label: "XGBoost", icon: Brain },
        { id: "history", label: "이력", icon: Images },
    ] as const;

    return (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-base font-bold text-slate-900">
                    AI 모델 판단 정보
                </h2>
                <div className="grid grid-cols-4 rounded-lg bg-slate-100 p-1">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            type="button"
                            onClick={() => setActiveTab(tab.id)}
                            className={cn(
                                "flex min-w-0 items-center justify-center gap-1.5 rounded-md px-2 py-1.5 text-xs font-semibold text-slate-500 transition-colors",
                                activeTab === tab.id &&
                                    "bg-white text-slate-900 shadow-sm",
                            )}
                        >
                            <tab.icon className="size-3.5 shrink-0" />
                            <span className="truncate">{tab.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            {activeTab === "summary" ? (
                <CurrentRiskCard drain={detailData.drain} meta={meta} compact />
            ) : null}
            {activeTab === "yolo" ? (
                <YoloAnalysisPanel detailData={detailData} />
            ) : null}
            {activeTab === "xgboost" ? (
                <XgboostAnalysisPanel detailData={detailData} />
            ) : null}
            {activeTab === "history" ? (
                <AnalysisHistoryPanel detailData={detailData} />
            ) : null}
        </div>
    );
}

function YoloAnalysisPanel({ detailData }: { detailData: DrainDetailData }) {
    const yoloResult = getLatestYoloResult(detailData);
    if (!yoloResult) {
        return <EmptyAnalysisState label="YOLO 분석 정보가 없습니다." />;
    }

    return (
        <dl className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <AnalysisInfoRow
                label="YOLO Result ID"
                value={formatNullable(yoloResult.id)}
            />
            <AnalysisInfoRow
                label="분석 상태"
                value={getYoloStatusLabel(yoloResult.yoloStatus)}
            />
            <AnalysisInfoRow
                label="막힘률"
                value={formatRatioPercent(yoloResult.obstructionRatio)}
            />
            <AnalysisInfoRow
                label="신뢰도"
                value={formatRatioPercent(yoloResult.confidenceScore)}
            />
            <AnalysisInfoRow
                label="촬영 시각"
                value={formatDisplayTime(yoloResult.capturedAt)}
            />
            <AnalysisInfoRow
                label="분석 시각"
                value={formatDisplayTime(yoloResult.analyzedAt)}
            />
        </dl>
    );
}

function XgboostAnalysisPanel({
    detailData,
}: {
    detailData: DrainDetailData;
}) {
    const xgboostResult = getLatestXgboostResult(detailData);
    if (!xgboostResult) {
        return <EmptyAnalysisState label="XGBoost 판단 정보가 없습니다." />;
    }

    return (
        <dl className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <AnalysisInfoRow
                label="XGBoost Result ID"
                value={formatNullable(xgboostResult.id)}
            />
            <AnalysisInfoRow
                label="위험 상태"
                value={<StatusBadge status={xgboostResult.riskLevel} />}
            />
            <AnalysisInfoRow
                label="위험 점수"
                value={`${riskScoreToPoint(xgboostResult.riskScore)}점`}
            />
            <AnalysisInfoRow
                label="참조 Sensor ID"
                value={formatNullable(xgboostResult.sensorDataId)}
            />
            <AnalysisInfoRow
                label="참조 YOLO ID"
                value={formatNullable(xgboostResult.yoloResultId)}
            />
            <AnalysisInfoRow
                label="판단 시각"
                value={formatDisplayTime(
                    xgboostResult.evaluatedAt ?? xgboostResult.predictedAt,
                )}
            />
            <div className="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 md:col-span-2">
                <dt className="text-xs font-medium text-slate-500">
                    최종 판단 문구
                </dt>
                <dd className="mt-1 text-sm font-semibold text-slate-800">
                    {xgboostResult.finalDecision ?? "-"}
                </dd>
            </div>
        </dl>
    );
}

function AnalysisHistoryPanel({
    detailData,
}: {
    detailData: DrainDetailData;
}) {
    const yoloResults = detailData.analysisHistory?.yoloResults ?? [];
    const xgboostResults = detailData.analysisHistory?.xgboostResults ?? [];

    if (yoloResults.length === 0 && xgboostResults.length === 0) {
        return <EmptyAnalysisState label="분석 이력 API 응답이 없습니다." />;
    }

    return (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <HistoryList
                title="YOLO 이미지 이력"
                items={yoloResults.map((item) => ({
                    key: `yolo-${item.id ?? item.analyzedAt}`,
                    title: `${formatRatioPercent(item.obstructionRatio)} / ${getYoloStatusLabel(item.yoloStatus)}`,
                    meta: formatDisplayTime(item.analyzedAt ?? item.createdAt),
                }))}
            />
            <HistoryList
                title="XGBoost 판단 이력"
                items={xgboostResults.map((item) => ({
                    key: `xgboost-${item.id ?? item.evaluatedAt}`,
                    title: `${riskScoreToPoint(item.riskScore)}점 / ${STATUS_META[item.riskLevel].label}`,
                    meta: formatDisplayTime(item.evaluatedAt ?? item.createdAt),
                }))}
            />
        </div>
    );
}

function AnalysisInfoRow({
    label,
    value,
}: {
    label: string;
    value: React.ReactNode;
}) {
    return (
        <div className="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2">
            <dt className="text-xs font-medium text-slate-500">{label}</dt>
            <dd className="mt-1 text-sm font-semibold text-slate-800">
                {value}
            </dd>
        </div>
    );
}

function EmptyAnalysisState({ label }: { label: string }) {
    return (
        <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center text-sm font-semibold text-slate-500">
            {label}
        </div>
    );
}

function HistoryList({
    title,
    items,
}: {
    title: string;
    items: { key: string; title: string; meta: string }[];
}) {
    return (
        <div>
            <h3 className="mb-2 text-sm font-bold text-slate-800">{title}</h3>
            <ul className="max-h-[220px] space-y-2 overflow-y-auto pr-1">
                {items.map((item) => (
                    <li
                        key={item.key}
                        className="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2"
                    >
                        <p className="text-sm font-semibold text-slate-800">
                            {item.title}
                        </p>
                        <p className="mt-0.5 text-xs text-slate-500">
                            {item.meta}
                        </p>
                    </li>
                ))}
            </ul>
        </div>
    );
}

function CurrentRiskCard({
    drain,
    meta,
    compact = false,
}: {
    drain: DrainDetailData["drain"];
    meta: (typeof STATUS_META)[RiskStatus];
    compact?: boolean;
}) {
    return (
        <div
            className={cn(
                !compact &&
                    "rounded-xl border border-slate-200 bg-white p-5 shadow-sm",
            )}
        >
            {!compact ? (
                <h2 className="mb-4 text-base font-bold text-slate-900">
                    현재 위험 상태
                </h2>
            ) : null}
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

function DetailUnavailableCard({
    title,
    description,
}: {
    title: string;
    description: string;
}) {
    return (
        <div className="rounded-xl border border-dashed border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-start gap-3">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
                    <AlertTriangle className="size-5" />
                </span>
                <div>
                    <h2 className="text-base font-bold text-slate-900">
                        {title}
                    </h2>
                    <p className="mt-1 text-sm text-slate-500">
                        {description}
                    </p>
                    <span className="mt-3 inline-flex rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-500">
                        mock fallback
                    </span>
                </div>
            </div>
        </div>
    );
}

function RiskHistoryUnavailableCard() {
    return (
        <div className="rounded-xl border border-dashed border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-base font-bold text-slate-900">
                과거 위험 이력
            </h2>
            <div className="rounded-lg bg-slate-50 px-4 py-5 text-center">
                <Clock className="mx-auto size-6 text-slate-400" />
                <p className="mt-2 text-sm font-bold text-slate-700">
                    위험 이력 연결 대기
                </p>
                <p className="mt-1 text-xs text-slate-500">
                    실제 위험 이력 API가 연결되면 이곳에 이력 row가 표시됩니다.
                </p>
            </div>
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

function getFallbackSensorSummary() {
    return {
        currentLevel: 0,
        currentFlow: 0,
        maxLevel: 0,
        maxLevelTime: "-",
        maxFlow: 0,
        maxFlowTime: "-",
    };
}

function getSensorSummary(points: DrainDetailData["sensorHistory"]) {
    const fallback = getFallbackSensorSummary();
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
    const yoloResults = [
        getLatestYoloResult(detailData),
        ...(detailData.analysisHistory?.yoloResults ?? []),
    ].filter(Boolean) as YoloResultDto[];
    const snapshots = yoloResults
        .map((item) => ({
            id: item.id,
            imageUrl: item.imageUrl ?? PLACEHOLDER_IMAGES.cctv,
            capturedAt:
                item.capturedAt ??
                item.analyzedAt ??
                item.createdAt ??
                detailData.drain.updatedAt,
            obstructionRatio: item.obstructionRatio,
            confidenceScore: item.confidenceScore,
            yoloStatus: item.yoloStatus,
        }))
        .filter(
            (item, index, array) =>
                array.findIndex(
                    (candidate) =>
                        candidate.imageUrl === item.imageUrl &&
                        candidate.capturedAt === item.capturedAt,
                ) === index,
        );

    if (snapshots.length > 0) return snapshots;

    return [
        {
            imageUrl: detailData.detail.imageUrl ?? PLACEHOLDER_IMAGES.cctv,
            capturedAt: detailData.drain.updatedAt,
        },
    ];
}

function getLatestYoloResult(
    detailData: DrainDetailData,
): YoloResultDto | undefined {
    return (
        detailData.analysisHistory?.yoloResults[0] ??
        detailData.analysis?.yoloResult ??
        detailData.detail.yoloResult
    );
}

function getLatestXgboostResult(
    detailData: DrainDetailData,
): XgboostResultDto | undefined {
    return (
        detailData.analysisHistory?.xgboostResults[0] ??
        detailData.analysis?.xgboostResult ??
        detailData.detail.xgboostResult
    );
}

function yoloEventToDto(event: YoloResultUpdatedEventDto): YoloResultDto {
    return {
        id: event.payload.yoloResultId,
        drainId: event.payload.drainId,
        imageUrl: event.payload.imageUrl,
        obstructionRatio: event.payload.obstructionRatio,
        confidenceScore: event.payload.confidenceScore,
        yoloStatus: event.payload.yoloStatus,
        capturedAt: event.payload.capturedAt,
        analyzedAt: event.payload.analyzedAt,
        createdAt: event.payload.updatedAt,
    };
}

function xgboostEventToDto(
    event: XgboostResultUpdatedEventDto,
): XgboostResultDto {
    return {
        id: event.payload.xgboostResultId,
        drainId: event.payload.drainId,
        sensorDataId: event.payload.sensorDataId,
        yoloResultId: event.payload.yoloResultId,
        riskLevel: event.payload.riskLevel,
        riskScore: event.payload.riskScore,
        finalDecision: event.payload.finalDecision,
        evaluatedAt: event.payload.evaluatedAt,
        createdAt: event.payload.updatedAt,
    };
}

function upsertYoloResult(items: YoloResultDto[], item: YoloResultDto) {
    return [
        item,
        ...items.filter((current) => current.id !== item.id),
    ].slice(0, 10);
}

function upsertXgboostResult(
    items: XgboostResultDto[],
    item: XgboostResultDto,
) {
    return [
        item,
        ...items.filter((current) => current.id !== item.id),
    ].slice(0, 10);
}

function ratioToPercent(value: number) {
    return Math.min(100, Math.max(0, Math.round(value <= 1 ? value * 100 : value)));
}

function riskScoreToPoint(value?: number | null) {
    if (value == null) return 0;
    return ratioToPercent(value);
}

function formatRatioPercent(value?: number | null) {
    if (value == null) return "-";
    return `${ratioToPercent(value)}%`;
}

function formatNullable(value?: number | string | null) {
    return value == null || value === "" ? "-" : String(value);
}

function formatDisplayTime(value?: string | null) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hour = String(date.getHours()).padStart(2, "0");
    const minute = String(date.getMinutes()).padStart(2, "0");
    return `${month}-${day} ${hour}:${minute}`;
}

function getYoloStatusLabel(status: YoloResultDto["yoloStatus"]) {
    const labels: Record<YoloResultDto["yoloStatus"], string> = {
        clear: "정상",
        partially_blocked: "부분 막힘",
        blocked: "막힘",
        unknown: "판단 불가",
    };
    return labels[status];
}

