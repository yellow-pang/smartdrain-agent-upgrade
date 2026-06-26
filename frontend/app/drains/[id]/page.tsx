"use client";

import Link from "next/link";
import { use, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { notFound } from "next/navigation";
import {
    AlertTriangle,
    ArrowLeft,
    Clock,
} from "lucide-react";
import { AppHeader } from "@/components/app-header";
import {
    DrainDetailErrorPage,
    DrainDetailLoadingPage,
    DrainDetailPageFrame,
    DrainDetailPageHeader,
} from "@/components/drain-detail/drain-detail-page-frame";
import { AnalysisSummaryCard } from "@/components/drain-detail/analysis-summary-card";
import { AiAnalysisTabs } from "@/components/drain-detail/ai-analysis-tabs";
import {
    CurrentRiskCard,
    LocationMapCard,
} from "@/components/drain-detail/drain-detail-status-panels";
import {
    FacilityInfoCard,
    RiskHistoryCard,
} from "@/components/drain-detail/facility-overview-panels";
import { CctvSnapshotCard } from "@/components/cctv-snapshot-card";
import { SensorTrendChart } from "@/components/sensor-trend-chart";
import { PlaceholderState } from "@/components/placeholder-state";
import { STATUS_META, type RiskStatus } from "@/lib/mock-data";
import {
    loadDrainDetailData,
    type DrainDetailData,
} from "@/lib/api/drain-data";
import { mergeDrainStatusEventIntoFacility } from "@/lib/api/adapters";
import { cn } from "@/lib/utils";
import { PLACEHOLDER_IMAGES } from "@/lib/placeholders";
import { useDrainStore } from "@/store/drain-store";
import { useDrainsQuery } from "@/lib/query/drain-queries";
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
    const [loadError, setLoadError] = useState<string | null>(null);
    const { data: drains } = useDrainsQuery();
    const sharedDrain = drains?.find((drain) => drain.id === id);
    const statusEvent = useDrainStore((state) => state.statusEventsByDrainId[id]);
    const yoloEvent = useDrainStore((state) => state.yoloEventsByDrainId[id]);
    const xgboostEvent = useDrainStore((state) => state.xgboostEventsByDrainId[id]);
    const socketStatus = useDrainStore((state) => state.socketStatus);
    const hasConnectedRef = useRef(false);
    const detailRequestIdRef = useRef(0);

    const applyRealtimeEvent = useCallback(
        (event: DrainStatusUpdatedEventDto) => {
            detailRequestIdRef.current += 1;
            setDetailData((current) => {
                if (
                    !current ||
                    current.source !== "api" ||
                    current.drain.id !== event.payload.drainId
                ) {
                    return current;
                }

                const xgboostResult = statusEventToXgboostDto(event);
                const sensorHistory = upsertSensorPoint(
                    current.sensorHistory,
                    sensorEventToPoint(event),
                );
                const riskHistory = upsertRiskHistoryItem(
                    current.riskHistory,
                    {
                        time: event.payload.updatedAt,
                        status: event.payload.riskLevel,
                        score: 0,
                    },
                );

                return {
                    ...current,
                    drain: mergeDrainStatusEventIntoFacility(
                        current.drain,
                        event,
                    ),
                    sensorHistory,
                    riskHistory,
                    analysis: {
                        ...current.analysis,
                        xgboostResult,
                        updatedAt: event.payload.updatedAt,
                    },
                    analysisHistory: {
                        drainId: event.payload.drainId,
                        yoloResults:
                            current.analysisHistory?.yoloResults ?? [],
                        xgboostResults: upsertXgboostResult(
                            current.analysisHistory?.xgboostResults ?? [],
                            xgboostResult,
                        ),
                    },
                };
            });
        },
        [],
    );

    const applyYoloEvent = useCallback((event: YoloResultUpdatedEventDto) => {
        detailRequestIdRef.current += 1;
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
            detailRequestIdRef.current += 1;
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
                            score: 0,
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
        const requestId = ++detailRequestIdRef.current;

        void loadDrainDetailData(id)
            .then((data) => {
                if (!mounted || requestId !== detailRequestIdRef.current) return;
                setLoadError(null);
                setDetailData(data);
            })
            .catch(() => {
                if (!mounted || requestId !== detailRequestIdRef.current) return;
                setLoadError("상세 데이터를 불러오지 못했습니다.");
            });

        return () => {
            mounted = false;
        };
    }, [id]);

    useEffect(() => {
        if (!statusEvent) return;
        const timer = window.setTimeout(
            () => applyRealtimeEvent(statusEvent),
            0,
        );
        return () => window.clearTimeout(timer);
    }, [applyRealtimeEvent, statusEvent]);

    useEffect(() => {
        if (!yoloEvent) return;
        const timer = window.setTimeout(() => applyYoloEvent(yoloEvent), 0);
        return () => window.clearTimeout(timer);
    }, [applyYoloEvent, yoloEvent]);

    useEffect(() => {
        if (!xgboostEvent) return;
        const timer = window.setTimeout(
            () => applyXgboostEvent(xgboostEvent),
            0,
        );
        return () => window.clearTimeout(timer);
    }, [applyXgboostEvent, xgboostEvent]);

    useEffect(() => {
        if (socketStatus !== "connected") return;
        if (!hasConnectedRef.current) {
            hasConnectedRef.current = true;
            return;
        }

        let mounted = true;
        const requestId = ++detailRequestIdRef.current;
        void loadDrainDetailData(id)
            .then((data) => {
                if (!mounted || requestId !== detailRequestIdRef.current) return;
                if (data) setDetailData(data);
            })
            .catch(() => undefined);

        return () => {
            mounted = false;
        };
    }, [id, socketStatus]);

    const drain = sharedDrain ?? detailData?.drain;
    const meta = drain ? STATUS_META[drain.status] : undefined;
    const sensorSummary = useMemo(() => {
        if (!detailData) return undefined;
        return getSensorSummary(detailData.sensorHistory, detailData.detail.sensorSummary);
    }, [detailData]);

    if (detailData === null) notFound();

    if (loadError) {
        return <DrainDetailErrorPage message={loadError} />;
    }

    if (!detailData || !drain || !meta || !sensorSummary) {
        return <DrainDetailLoadingPage />;
    }

    return (
        <DrainDetailPageFrame>
            <DrainDetailPageHeader drain={drain} />

                <AnalysisSummaryCard
                    drain={detailData.drain}
                    obstructionPercent={getObstructionPercent(detailData)}
                    finalDecision={getLatestXgboostResult(detailData)?.finalDecision}
                    evaluatedAt={
                        getLatestXgboostResult(detailData)?.evaluatedAt ??
                        getLatestXgboostResult(detailData)?.predictedAt
                    }
                />

            <div className="mt-5 grid grid-cols-1 gap-4 xl:grid-cols-12">
                    {/* Left column */}
                    <div className="flex flex-col gap-4 xl:col-span-4">
                        <CctvSnapshotCard
                            snapshots={getSnapshots(detailData)}
                            locationName={drain.road}
                        />
                        <LocationMapCard
                            drain={drain}
                            source={detailData.source}
                        />
                    </div>

                    {/* Middle column */}
                    <div className="flex flex-col gap-4 xl:col-span-5">
                        <SensorTrendChart
                            points={detailData.sensorHistory}
                            summary={sensorSummary}
                        />
                        <AiAnalysisTabs
                            summary={<CurrentRiskCard drain={detailData.drain} compact />}
                            yoloResult={getLatestYoloResult(detailData)}
                            xgboostResult={getLatestXgboostResult(detailData)}
                            yoloResults={detailData.analysisHistory?.yoloResults ?? []}
                            xgboostResults={detailData.analysisHistory?.xgboostResults ?? []}
                        />
                    </div>

                    {/* Right column */}
                    <div className="flex flex-col gap-4 xl:col-span-3">
                        <FacilityInfoCard drain={drain} />
                        <RiskHistoryCard riskHistory={detailData.riskHistory} />
                    </div>
            </div>
        </DrainDetailPageFrame>
    );
}

function DrainDetailFallbackPage({ drainId }: { drainId: string }) {
    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
            <AppHeader />

            <main className="mx-auto max-w-[1600px] p-4 md:p-6">
                <Link
                    href="/"
                    className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                >
                    <ArrowLeft className="size-4" />
                    대시보드로 돌아가기
                </Link>

                <div className="mt-2 flex flex-wrap items-baseline gap-3">
                    <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl dark:text-slate-100">
                        하수구 상세 정보
                    </h1>
                    <span className="text-sm font-medium text-slate-500 dark:text-slate-400">
                        {drainId}
                    </span>
                    <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-400">
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
                            description="상세 API가 연결되면 상태, 막힘 정도, 수위, 유속이 표시됩니다."
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

function DetailUnavailableCard({
    title,
    description,
}: {
    title: string;
    description: string;
}) {
    return (
        <div className="rounded-xl border border-dashed border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <div className="flex items-start gap-3">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                    <AlertTriangle className="size-5" />
                </span>
                <div>
                    <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
                        {title}
                    </h2>
                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                        {description}
                    </p>
                    <span className="mt-3 inline-flex rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                        mock fallback
                    </span>
                </div>
            </div>
        </div>
    );
}

function RiskHistoryUnavailableCard() {
    return (
        <div className="rounded-xl border border-dashed border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <h2 className="mb-3 text-base font-bold text-slate-900 dark:text-slate-100">
                과거 위험 이력
            </h2>
            <div className="rounded-lg bg-slate-50 px-4 py-5 text-center dark:bg-slate-800/70">
                <Clock className="mx-auto size-6 text-slate-400 dark:text-slate-500" />
                <p className="mt-2 text-sm font-bold text-slate-700 dark:text-slate-200">
                    위험 이력 연결 대기
                </p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    실제 위험 이력 API가 연결되면 이곳에 이력 row가 표시됩니다.
                </p>
            </div>
        </div>
    );
}

function getFallbackSensorSummary() {
    return {
        currentLevel: 0,
        currentFlow: 0,
    };
}

function getSensorSummary(
    points: DrainDetailData["sensorHistory"],
    sensorSummary?: DrainDetailData["detail"]["sensorSummary"],
) {
    const fallback = getFallbackSensorSummary();
    if (sensorSummary) {
        return {
            currentLevel: sensorSummary.waterLevelCm,
            currentFlow: sensorSummary.flowVelocityMps,
        };
    }
    if (points.length === 0) return fallback;

    const latest = points[points.length - 1];
    return {
        currentLevel: latest.level,
        currentFlow: latest.flow,
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

function getObstructionPercent(detailData: DrainDetailData) {
    const yoloResult = getLatestYoloResult(detailData);
    return yoloResult?.obstructionRatio == null
        ? detailData.drain.blockage
        : ratioToPercent(yoloResult.obstructionRatio);
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

function statusEventToXgboostDto(
    event: DrainStatusUpdatedEventDto,
): XgboostResultDto {
    return {
        id: event.payload.xgboostResultId ?? undefined,
        drainId: event.payload.drainId,
        sensorDataId: event.payload.sensorDataId,
        yoloResultId: event.payload.yoloResultId,
        riskLevel: event.payload.riskLevel,
        riskScore: event.payload.riskScore,
        finalDecision: event.payload.finalDecision ?? null,
        evaluatedAt: event.payload.updatedAt,
        createdAt: event.payload.updatedAt,
    };
}

function sensorEventToPoint(event: DrainStatusUpdatedEventDto) {
    const { waterLevelCm, flowVelocityMps, updatedAt } = event.payload;
    if (waterLevelCm == null || flowVelocityMps == null) return null;

    return {
        time: formatSensorChartTime(updatedAt),
        level: waterLevelCm,
        flow: flowVelocityMps,
    };
}

function upsertSensorPoint(
    points: DrainDetailData["sensorHistory"],
    point: DrainDetailData["sensorHistory"][number] | null,
) {
    if (!point) return points;
    return [...points.filter((current) => current.time !== point.time), point]
        .sort((a, b) => a.time.localeCompare(b.time))
        .slice(-48);
}

function upsertRiskHistoryItem(
    items: DrainDetailData["riskHistory"],
    item: DrainDetailData["riskHistory"][number],
) {
    return [item, ...items.filter((current) => current.time !== item.time)].slice(0, 10);
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

function formatSensorChartTime(value: string) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hour = String(date.getHours()).padStart(2, "0");
    const minute = String(date.getMinutes()).padStart(2, "0");
    const second = String(date.getSeconds()).padStart(2, "0");
    return `${month}-${day} ${hour}:${minute}:${second}`;
}

function ratioToPercent(value: number) {
    return Math.min(100, Math.max(0, Math.round(value <= 1 ? value * 100 : value)));
}

