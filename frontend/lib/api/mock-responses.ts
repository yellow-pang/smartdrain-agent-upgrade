import type {
    AnalysisResultDto,
    ApiListResponse,
    ApiResponse,
    DashboardSummaryDto,
    DrainAnalysisHistoryResponse,
    DrainDetailDto,
    DrainListItemDto,
    RiskHistoryDto,
    SensorHistoryDto,
    XgboostResultDto,
    YoloResultDto,
    YoloStatus,
} from "@/lib/api/types";
import { DRAINS, type DrainFacility } from "@/lib/mock-data";
import { PLACEHOLDER_IMAGES } from "@/lib/placeholders";

const BASE_DATE = "2026-06-18";
const CCTV_IMAGE_URL = PLACEHOLDER_IMAGES.cctv;

export function createMockDrainListResponse(): ApiListResponse<DrainListItemDto> {
    const items = DRAINS.map(facilityToListItemDto);
    return {
        success: true,
        data: {
            items,
            totalCount: items.length,
        },
        timestamp: `${BASE_DATE}T09:30:01+09:00`,
    };
}

export function createMockDrainDetailResponse(
    id: string,
): ApiResponse<DrainDetailDto> {
    const drain = DRAINS.find((item) => item.id === id);
    if (!drain) {
        return {
            success: false,
            data: null,
            message: "요청한 빗물받이를 찾을 수 없습니다.",
            error: {
                code: "DRAIN_NOT_FOUND",
                message: "Drain not found",
                detail: { id },
            },
            timestamp: `${BASE_DATE}T09:30:01+09:00`,
        };
    }

    return {
        success: true,
        data: {
            ...facilityToListItemDto(drain),
            imageUrl: CCTV_IMAGE_URL,
            sensorSummary: {
                waterLevelCm: Math.round(drain.waterLevelM * 100),
                flowVelocityMps: drain.flow,
                measuredAt: toIsoTime(drain.updatedAt),
            },
            sensorHistory: createMockSensorHistoryItems(drain),
            yoloResult: createMockYoloResult(drain),
            xgboostResult: {
                riskScore: drain.blockage / 100,
                riskLevel: drain.status,
                finalDecision: drain.judgement,
                predictedAt: toIsoTime(drain.updatedAt),
            },
            riskHistory: createMockRiskHistoryItems(drain),
        },
        timestamp: `${BASE_DATE}T09:30:01+09:00`,
    };
}

export function createMockSensorHistoryResponse(
    id: string,
): ApiListResponse<SensorHistoryDto> {
    const detail = createMockDrainDetailResponse(id);
    const items = detail.data?.sensorHistory ?? [];
    return {
        success: true,
        data: {
            items,
            totalCount: items.length,
        },
        timestamp: `${BASE_DATE}T09:30:01+09:00`,
    };
}

export function createMockRiskHistoryResponse(
    id: string,
): ApiListResponse<RiskHistoryDto> {
    const detail = createMockDrainDetailResponse(id);
    const items = detail.data?.riskHistory ?? [];
    return {
        success: true,
        data: {
            items,
            totalCount: items.length,
        },
        timestamp: `${BASE_DATE}T09:30:01+09:00`,
    };
}

export function createMockDashboardSummaryResponse(): ApiResponse<DashboardSummaryDto> {
    return {
        success: true,
        data: {
            totalCount: DRAINS.length,
            goodCount: DRAINS.filter((drain) => drain.status === "good").length,
            cautionCount: DRAINS.filter((drain) => drain.status === "caution")
                .length,
            dangerCount: DRAINS.filter((drain) => drain.status === "danger")
                .length,
            unknownCount: DRAINS.filter((drain) => drain.status === "unknown")
                .length,
            latestUpdatedAt: `${BASE_DATE}T09:30:00+09:00`,
        },
        timestamp: `${BASE_DATE}T09:30:01+09:00`,
    };
}

export function createMockLatestAnalysisResponse(
    id: string,
): ApiResponse<AnalysisResultDto> {
    const detail = createMockDrainDetailResponse(id);
    return {
        success: detail.success,
        data: detail.data
            ? {
                  sensorSummary: detail.data.sensorSummary,
                  yoloResult: detail.data.yoloResult,
                  xgboostResult: detail.data.xgboostResult,
                  updatedAt: detail.data.updatedAt,
              }
            : null,
        message: detail.message,
        error: detail.error,
        timestamp: detail.timestamp,
    };
}

export function createMockAnalysisHistoryResponse(
    id: string,
): ApiResponse<DrainAnalysisHistoryResponse> {
    const detail = createMockDrainDetailResponse(id);
    const drain = DRAINS.find((item) => item.id === id);
    if (!detail.success || !detail.data || !drain) {
        return {
            success: false,
            data: null,
            message: detail.message,
            error: detail.error,
            timestamp: detail.timestamp,
        };
    }

    const yoloResults = createMockYoloHistoryItems(drain);
    const xgboostResults = createMockXgboostHistoryItems(drain, yoloResults);

    return {
        success: true,
        data: {
            drainId: id,
            yoloResults,
            xgboostResults,
        },
        timestamp: `${BASE_DATE}T09:30:01+09:00`,
    };
}

function facilityToListItemDto(drain: DrainFacility): DrainListItemDto {
    return {
        id: drain.id,
        roadAddress: drain.road,
        fullAddress: drain.fullAddress,
        latitude: drain.latitude,
        longitude: drain.longitude,
        riskLevel: drain.status,
        riskScore: drain.blockage / 100,
        obstructionRatio: drain.blockage / 100,
        waterLevelCm: Math.round(drain.waterLevelM * 100),
        flowVelocityMps: drain.flow,
        finalDecision: drain.judgement,
        updatedAt: toIsoTime(drain.updatedAt),
    };
}

function createMockSensorHistoryItems(drain: DrainFacility): SensorHistoryDto[] {
    return Array.from({ length: 12 }, (_, index) => {
        const hour = 4 + index * 2;
        const wave = Math.sin((index / 11) * Math.PI);
        return {
            measuredAt: `${BASE_DATE}T${String(hour).padStart(2, "0")}:00:00+09:00`,
            waterLevelCm: Math.round(drain.waterLevelM * 100 * (0.55 + wave * 0.5)),
            flowVelocityMps: +(drain.flow * (0.6 + wave * 0.5)).toFixed(2),
        };
    });
}

function createMockRiskHistoryItems(drain: DrainFacility): RiskHistoryDto[] {
    const levels = [
        drain.status,
        drain.status === "danger" ? "caution" : drain.status,
        "good",
        "caution",
        "good",
    ] as const;

    return levels.map((riskLevel, index) => ({
        changedAt: `${BASE_DATE}T${String(9 + index * 2).padStart(2, "0")}:20:00+09:00`,
        riskLevel,
        riskScore: Math.max(0.08, drain.blockage / 100 - index * 0.12),
    }));
}

function createMockYoloResult(drain: DrainFacility) {
    const yoloStatus: YoloStatus =
        drain.blockage >= 80
            ? "blocked"
            : drain.blockage >= 40
              ? "partially_blocked"
              : "clear";

    return {
        imageUrl: CCTV_IMAGE_URL,
        obstructionRatio: drain.blockage / 100,
        confidenceScore: drain.status === "unknown" ? 0.42 : 0.91,
        yoloStatus,
        capturedAt: toIsoTime(drain.updatedAt),
        analyzedAt: toIsoTime(drain.updatedAt),
    };
}

function createMockYoloHistoryItems(drain: DrainFacility): YoloResultDto[] {
    const images = [
        PLACEHOLDER_IMAGES.cctv,
        "/test-snapshots/drain-001-a.jpg",
        "/test-snapshots/drain-001-b.jpg",
        "/test-snapshots/drain-001-c.jpg",
    ];

    return images.map((imageUrl, index) => {
        const obstructionRatio = Math.max(
            0.05,
            drain.blockage / 100 - index * 0.12,
        );
        return {
            id: index + 1,
            drainId: drain.id,
            imageUrl,
            obstructionRatio,
            confidenceScore: Math.max(0.5, 0.92 - index * 0.06),
            yoloStatus: getYoloStatus(obstructionRatio),
            capturedAt: `${BASE_DATE}T${String(14 - index).padStart(2, "0")}:10:00+09:00`,
            analyzedAt: `${BASE_DATE}T${String(14 - index).padStart(2, "0")}:10:01+09:00`,
            createdAt: `${BASE_DATE}T${String(14 - index).padStart(2, "0")}:10:01+09:00`,
        };
    });
}

function createMockXgboostHistoryItems(
    drain: DrainFacility,
    yoloResults: YoloResultDto[],
): XgboostResultDto[] {
    return yoloResults.slice(0, 3).map((yoloResult, index) => {
        const riskScore = Math.max(0.06, drain.blockage / 100 - index * 0.15);
        return {
            id: index + 1,
            drainId: drain.id,
            sensorDataId: index + 1,
            yoloResultId: yoloResult.id ?? null,
            riskScore,
            riskLevel:
                riskScore >= 0.7
                    ? "danger"
                    : riskScore >= 0.35
                      ? "caution"
                      : "good",
            finalDecision:
                index === 0 ? drain.judgement : "최근 분석 이력 mock 데이터",
            evaluatedAt: `${BASE_DATE}T${String(14 - index).padStart(2, "0")}:15:00+09:00`,
            createdAt: `${BASE_DATE}T${String(14 - index).padStart(2, "0")}:15:00+09:00`,
        };
    });
}

function getYoloStatus(value: number): YoloStatus {
    if (value >= 0.7) return "blocked";
    if (value >= 0.35) return "partially_blocked";
    return "clear";
}

function toIsoTime(value: string) {
    if (value.includes("T")) return value;
    return `${value.replace(" ", "T")}:00+09:00`;
}
