"use client";

import { useMemo, useState } from "react";
import { Info } from "lucide-react";
import {
    CartesianGrid,
    Line,
    LineChart,
    ReferenceLine,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import { cn } from "@/lib/utils";
import { SENSOR_THRESHOLDS, type SensorPoint } from "@/lib/mock-data";
import { StatusBadge } from "@/components/status-badge";
import { PlaceholderState } from "@/components/placeholder-state";
import { PLACEHOLDER_IMAGES } from "@/lib/placeholders";

type RangeKey = "24h" | "7d";

type SensorSummary = {
    currentLevel: number;
    currentFlow: number;
    maxLevel: number;
    maxLevelTime: string;
    maxFlow: number;
    maxFlowTime: string;
};

export function SensorTrendChart({
    points,
    summary,
    isFallback = false,
}: {
    points: SensorPoint[];
    summary: SensorSummary;
    isFallback?: boolean;
}) {
    const [range, setRange] = useState<RangeKey>("24h");
    const chartData = useMemo(() => {
        if (range === "24h") return points;
        return points.filter((_, index) => index % 2 === 0);
    }, [points, range]);

    return (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                    <h2 className="text-base font-bold text-slate-900">
                        센서 데이터 추세
                    </h2>
                    <Info className="size-3.5 text-slate-400" />
                </div>
                <div className="flex rounded-lg border border-slate-200 p-0.5">
                    {(["24h", "7d"] as RangeKey[]).map((key) => (
                        <button
                            key={key}
                            onClick={() => setRange(key)}
                            className={cn(
                                "rounded-md px-3 py-1 text-xs font-semibold transition-colors",
                                range === key
                                    ? "bg-cyan-700 text-white"
                                    : "text-slate-500 hover:text-slate-700",
                            )}
                        >
                            {key === "24h" ? "24시간" : "7일"}
                        </button>
                    ))}
                </div>
            </div>

            {/* legend */}
            <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-slate-500">
                <LegendItem color="#0e7490" label="수위 (m)" />
                <LegendItem color="#059669" label="유량 (m³/min)" />
                <LegendItem
                    color="#dc2626"
                    dashed
                    label={`위험 수위 ${SENSOR_THRESHOLDS.dangerLevel.toFixed(2)}m`}
                />
                <LegendItem
                    color="#d97706"
                    dashed
                    label={`주의 수위 ${SENSOR_THRESHOLDS.warningLevel.toFixed(2)}m`}
                />
            </div>

            {isFallback ? (
                <PlaceholderState
                    image={PLACEHOLDER_IMAGES.chart}
                    title="실시간 센서 데이터 연결 대기"
                    description="백엔드 센서 이력이 도착하면 수위와 유량 차트가 표시됩니다."
                    statusLabel="mock fallback"
                    className="mt-2 h-[280px]"
                />
            ) : (
                <div className="mt-2 h-[280px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart
                            data={chartData}
                            margin={{ top: 10, right: 8, left: -16, bottom: 0 }}
                        >
                            <CartesianGrid
                                strokeDasharray="3 3"
                                stroke="#f1f5f9"
                                vertical={false}
                            />
                            <XAxis
                                dataKey="time"
                                tick={{ fontSize: 11, fill: "#94a3b8" }}
                                tickLine={false}
                                axisLine={{ stroke: "#e2e8f0" }}
                                interval={range === "24h" ? 2 : 0}
                            />
                            <YAxis
                                tick={{ fontSize: 11, fill: "#94a3b8" }}
                                tickLine={false}
                                axisLine={false}
                                domain={[0, 2.5]}
                            />
                            <Tooltip content={<ChartTooltip />} />
                            <ReferenceLine
                                y={SENSOR_THRESHOLDS.dangerLevel}
                                stroke="#dc2626"
                                strokeDasharray="5 4"
                                strokeWidth={1.5}
                            />
                            <ReferenceLine
                                y={SENSOR_THRESHOLDS.warningLevel}
                                stroke="#d97706"
                                strokeDasharray="5 4"
                                strokeWidth={1.5}
                            />
                            {range === "24h" && (
                                <ReferenceLine
                                    x="14:30"
                                    stroke="#64748b"
                                    strokeWidth={1.5}
                                />
                            )}
                            <Line
                                type="monotone"
                                dataKey="level"
                                name="수위"
                                stroke="#0e7490"
                                strokeWidth={2}
                                dot={false}
                                isAnimationActive={false}
                            />
                            <Line
                                type="monotone"
                                dataKey="flow"
                                name="유량"
                                stroke="#059669"
                                strokeWidth={2}
                                dot={false}
                                isAnimationActive={false}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Summary cards */}
            <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
                <SummaryCard
                    label="현재 수위"
                    value={`${summary.currentLevel} m`}
                    badge="danger"
                />
                <SummaryCard
                    label="현재 유량"
                    value={`${summary.currentFlow} m³/min`}
                    badge="caution"
                />
                <SummaryCard
                    label="최고 수위 (24h)"
                    value={`${summary.maxLevel} m`}
                    sub={summary.maxLevelTime}
                />
                <SummaryCard
                    label="최고 유량 (24h)"
                    value={`${summary.maxFlow} m³/min`}
                    sub={summary.maxFlowTime}
                />
            </div>
        </div>
    );
}

function LegendItem({
    color,
    label,
    dashed,
}: {
    color: string;
    label: string;
    dashed?: boolean;
}) {
    return (
        <span className="flex items-center gap-1.5">
            <span
                className="inline-block h-0 w-4"
                style={{
                    borderTop: `2px ${dashed ? "dashed" : "solid"} ${color}`,
                }}
            />
            {label}
        </span>
    );
}

function SummaryCard({
    label,
    value,
    badge,
    sub,
}: {
    label: string;
    value: string;
    badge?: "danger" | "caution";
    sub?: string;
}) {
    return (
        <div className="rounded-lg border border-slate-100 bg-slate-50/60 px-3 py-2.5">
            <p className="text-xs text-slate-500">{label}</p>
            <div className="mt-1 flex items-center gap-2">
                <span className="text-lg font-bold text-slate-900">
                    {value}
                </span>
                {badge && <StatusBadge status={badge} />}
            </div>
            {sub && <p className="mt-0.5 text-xs text-slate-400">{sub}</p>}
        </div>
    );
}

function ChartTooltip({
    active,
    payload,
    label,
}: {
    active?: boolean;
    payload?: {
        dataKey: string;
        name: string;
        value: number;
        color: string;
    }[];
    label?: string;
}) {
    if (!active || !payload?.length) return null;
    return (
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-md">
            <p className="mb-1 text-xs font-semibold text-slate-700">{label}</p>
            {payload.map((entry) => (
                <p
                    key={entry.dataKey}
                    className="flex items-center gap-1.5 text-xs text-slate-600"
                >
                    <span
                        className="size-2 rounded-full"
                        style={{ background: entry.color }}
                    />
                    {entry.name}:{" "}
                    <span className="font-semibold">{entry.value}</span>
                </p>
            ))}
        </div>
    );
}
