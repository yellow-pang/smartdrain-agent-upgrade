// Mock data layer for the city flood management dashboard.
// Designed to be easy to swap with a real API later.

export type RiskStatus = "danger" | "warning" | "normal" | "unknown";

export interface DrainFacility {
    id: string;
    road: string;
    fullAddress: string;
    status: RiskStatus;
    blockage: number; // 막힘 정도 (%)
    waterLevelPct: number; // 수위 (%)
    waterLevelM: number; // 수위 (m)
    flow: number; // 유량 (m³/min)
    updatedAt: string;
    judgement: string; // 판정 결과
    // normalized position on the mock map (0-100)
    x: number;
    y: number;
}

export interface RiskHistoryItem {
    time: string;
    status: RiskStatus;
    score: number;
}

export interface SensorPoint {
    time: string; // "HH:MM"
    level: number; // 수위 (m)
    flow: number; // 유량 (m³/min)
}

export const STATUS_META: Record<
    RiskStatus,
    {
        label: string;
        dot: string;
        badgeClass: string;
        bar: string;
        text: string;
    }
> = {
    danger: {
        label: "위험",
        dot: "bg-red-500",
        badgeClass: "bg-red-50 text-red-600 border-red-200",
        bar: "bg-red-500",
        text: "text-red-600",
    },
    warning: {
        label: "주의",
        dot: "bg-amber-500",
        badgeClass: "bg-amber-50 text-amber-600 border-amber-200",
        bar: "bg-amber-500",
        text: "text-amber-600",
    },
    normal: {
        label: "정상",
        dot: "bg-emerald-500",
        badgeClass: "bg-emerald-50 text-emerald-600 border-emerald-200",
        bar: "bg-emerald-500",
        text: "text-emerald-600",
    },
    unknown: {
        label: "판단불가",
        dot: "bg-slate-400",
        badgeClass: "bg-slate-100 text-slate-500 border-slate-200",
        bar: "bg-slate-400",
        text: "text-slate-500",
    },
};

export const DRAINS: DrainFacility[] = [
    {
        id: "DR-004",
        road: "테헤란로 123",
        fullAddress: "서울특별시 강남구 테헤란로 123 (역삼동 123-45)",
        status: "danger",
        blockage: 85,
        waterLevelPct: 85,
        waterLevelM: 1.32,
        flow: 1.35,
        updatedAt: "2024-05-23 14:30",
        judgement: "침수 가능성 높음",
        x: 52,
        y: 50,
    },
    {
        id: "DR-011",
        road: "역삼로 88",
        fullAddress: "서울특별시 강남구 역삼로 88",
        status: "warning",
        blockage: 52,
        waterLevelPct: 48,
        waterLevelM: 0.78,
        flow: 0.92,
        updatedAt: "2024-05-23 14:25",
        judgement: "지속 관찰 필요",
        x: 30,
        y: 38,
    },
    {
        id: "DR-015",
        road: "삼성로 45",
        fullAddress: "서울특별시 강남구 삼성로 45",
        status: "warning",
        blockage: 41,
        waterLevelPct: 36,
        waterLevelM: 0.62,
        flow: 0.71,
        updatedAt: "2024-05-23 14:20",
        judgement: "지속 관찰 필요",
        x: 60,
        y: 62,
    },
    {
        id: "DR-018",
        road: "선릉로 52",
        fullAddress: "서울특별시 강남구 선릉로 52",
        status: "normal",
        blockage: 18,
        waterLevelPct: 22,
        waterLevelM: 0.38,
        flow: 0.42,
        updatedAt: "2024-05-23 14:18",
        judgement: "정상 범위",
        x: 18,
        y: 52,
    },
    {
        id: "DR-027",
        road: "삼성로 101",
        fullAddress: "서울특별시 강남구 삼성로 101",
        status: "normal",
        blockage: 12,
        waterLevelPct: 15,
        waterLevelM: 0.26,
        flow: 0.31,
        updatedAt: "2024-05-23 14:15",
        judgement: "정상 범위",
        x: 42,
        y: 72,
    },
    {
        id: "DR-033",
        road: "학동로 77",
        fullAddress: "서울특별시 강남구 학동로 77",
        status: "normal",
        blockage: 9,
        waterLevelPct: 10,
        waterLevelM: 0.18,
        flow: 0.22,
        updatedAt: "2024-05-23 14:12",
        judgement: "정상 범위",
        x: 24,
        y: 78,
    },
    {
        id: "DR-041",
        road: "도곡로 12",
        fullAddress: "서울특별시 강남구 도곡로 12",
        status: "normal",
        blockage: 14,
        waterLevelPct: 17,
        waterLevelM: 0.29,
        flow: 0.34,
        updatedAt: "2024-05-23 14:10",
        judgement: "정상 범위",
        x: 14,
        y: 70,
    },
    {
        id: "DR-052",
        road: "언주로 200",
        fullAddress: "서울특별시 강남구 언주로 200",
        status: "warning",
        blockage: 38,
        waterLevelPct: 33,
        waterLevelM: 0.57,
        flow: 0.66,
        updatedAt: "2024-05-23 14:08",
        judgement: "지속 관찰 필요",
        x: 70,
        y: 30,
    },
    {
        id: "DR-066",
        road: "봉은사로 50",
        fullAddress: "서울특별시 강남구 봉은사로 50",
        status: "normal",
        blockage: 11,
        waterLevelPct: 13,
        waterLevelM: 0.22,
        flow: 0.27,
        updatedAt: "2024-05-23 14:05",
        judgement: "정상 범위",
        x: 78,
        y: 58,
    },
    {
        id: "DR-070",
        road: "테헤란로 411",
        fullAddress: "서울특별시 강남구 테헤란로 411",
        status: "normal",
        blockage: 16,
        waterLevelPct: 19,
        waterLevelM: 0.33,
        flow: 0.39,
        updatedAt: "2024-05-23 14:02",
        judgement: "정상 범위",
        x: 86,
        y: 44,
    },
];

export function getDrainById(id: string): DrainFacility | undefined {
    return DRAINS.find((d) => d.id === id);
}

export const RISK_RANK: Record<RiskStatus, number> = {
    danger: 3,
    warning: 2,
    unknown: 1,
    normal: 0,
};

export function sortByRisk(drains: DrainFacility[]): DrainFacility[] {
    return [...drains].sort((a, b) => {
        const r = RISK_RANK[b.status] - RISK_RANK[a.status];
        if (r !== 0) return r;
        return b.blockage - a.blockage;
    });
}

export const LEGEND_COUNTS = {
    danger: DRAINS.filter((d) => d.status === "danger").length,
    warning: DRAINS.filter((d) => d.status === "warning").length,
    normal: DRAINS.filter((d) => d.status === "normal").length,
};

export const RISK_HISTORY: RiskHistoryItem[] = [
    { time: "2024-05-23 14:20", status: "danger", score: 82 },
    { time: "2024-05-23 09:10", status: "warning", score: 46 },
    { time: "2024-05-22 18:40", status: "normal", score: 18 },
    { time: "2024-05-22 12:20", status: "warning", score: 42 },
    { time: "2024-05-21 08:30", status: "normal", score: 15 },
    { time: "2024-05-20 17:50", status: "normal", score: 12 },
    { time: "2024-05-20 09:20", status: "normal", score: 10 },
];

export const SENSOR_THRESHOLDS = {
    dangerLevel: 1.5,
    warningLevel: 0.8,
};

export const SENSOR_SUMMARY = {
    currentLevel: 1.32,
    currentFlow: 1.35,
    maxLevel: 1.78,
    maxLevelTime: "13:42",
    maxFlow: 2.1,
    maxFlowTime: "13:47",
};

// Generates a smooth 24h sensor series (00:00 -> 24:00 in 30-min steps)
// peaking around mid-afternoon, with a danger crossing near 14:30.
export function generate24hSeries(seed = 0): SensorPoint[] {
    const points: SensorPoint[] = [];
    for (let i = 0; i <= 48; i++) {
        const hour = i * 0.5;
        const hh = String(Math.floor(hour)).padStart(2, "0");
        const mm = hour % 1 === 0 ? "00" : "30";
        // bell-ish curve centred near 16:00
        const wave = Math.sin(((hour - 4) / 24) * Math.PI);
        const base = Math.max(0, wave);
        const jitter = Math.sin((hour + seed) * 1.7) * 0.05;
        const level = +(0.55 + base * 1.55 + jitter).toFixed(2);
        const flow = +(0.25 + base * 1.7 + jitter * 1.2).toFixed(2);
        points.push({
            time: `${hh}:${mm}`,
            level: Math.max(0, level),
            flow: Math.max(0, flow),
        });
    }
    return points;
}

export function generate7dSeries(): SensorPoint[] {
    const days = [
        "05-17",
        "05-18",
        "05-19",
        "05-20",
        "05-21",
        "05-22",
        "05-23",
    ];
    const levels = [0.42, 0.55, 0.71, 0.48, 0.83, 1.12, 1.32];
    const flows = [0.38, 0.51, 0.79, 0.44, 0.91, 1.34, 1.35];
    return days.map((d, i) => ({ time: d, level: levels[i], flow: flows[i] }));
}
