export type RiskLevel = "good" | "caution" | "danger" | "unknown";

export const STATUS_META: Record<
    RiskLevel,
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
    caution: {
        label: "주의",
        dot: "bg-amber-500",
        badgeClass: "bg-amber-50 text-amber-600 border-amber-200",
        bar: "bg-amber-500",
        text: "text-amber-600",
    },
    good: {
        label: "양호",
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

export const RISK_RANK: Record<RiskLevel, number> = {
    danger: 3,
    caution: 2,
    unknown: 1,
    good: 0,
};
