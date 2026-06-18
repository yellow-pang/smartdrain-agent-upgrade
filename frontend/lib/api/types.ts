import type { RiskLevel } from "@/lib/risk";

export type YoloStatus = "clear" | "partially_blocked" | "blocked" | "unknown";

export type ApiResponse<T> = {
    success: boolean;
    data: T | null;
    message?: string;
    error?: {
        code: string;
        message: string;
        detail?: unknown;
    };
    timestamp?: string;
};

export type ApiListResponse<T> = ApiResponse<{
    items: T[];
    totalCount: number;
}>;

export type DrainListItemDto = {
    id: string;
    roadAddress: string;
    fullAddress?: string;
    latitude: number;
    longitude: number;
    riskLevel: RiskLevel;
    riskScore: number;
    obstructionRatio: number;
    waterLevelCm: number;
    flowVelocityMps: number;
    finalDecision: string;
    updatedAt: string;
};

export type DrainDetailDto = DrainListItemDto & {
    imageUrl?: string;
    sensorSummary?: SensorSummaryDto;
    sensorHistory?: SensorHistoryDto[];
    yoloResult?: YoloResultDto;
    xgboostResult?: XgboostResultDto;
    riskHistory?: RiskHistoryDto[];
};

export type SensorSummaryDto = {
    waterLevelCm: number;
    flowVelocityMps: number;
    measuredAt: string;
};

export type SensorHistoryDto = {
    measuredAt: string;
    waterLevelCm: number;
    flowVelocityMps: number;
};

export type YoloResultDto = {
    imageUrl?: string;
    obstructionRatio: number;
    confidenceScore: number;
    yoloStatus: YoloStatus;
    analyzedAt: string;
};

export type XgboostResultDto = {
    riskScore: number;
    riskLevel: RiskLevel;
    finalDecision: string;
    predictedAt: string;
};

export type RiskHistoryDto = {
    changedAt: string;
    riskLevel: RiskLevel;
    riskScore: number;
};

export type AnalysisResultDto = {
    sensorSummary?: SensorSummaryDto;
    yoloResult?: YoloResultDto;
    xgboostResult?: XgboostResultDto;
    updatedAt?: string;
};

export type DashboardSummaryDto = {
    totalCount: number;
    goodCount: number;
    cautionCount: number;
    dangerCount: number;
    unknownCount: number;
    latestUpdatedAt?: string;
};

export type DrainStatusUpdatedEventDto = {
    type: "DRAIN_STATUS_UPDATED";
    payload: {
        drainId: string;
        riskLevel: RiskLevel;
        riskScore: number;
        waterLevelCm?: number;
        flowVelocityMps?: number;
        obstructionRatio?: number;
        finalDecision?: string;
        updatedAt: string;
    };
};
