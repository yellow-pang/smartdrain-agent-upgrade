import {
    dashboardSummaryFromDrains,
    drainDetailDtoToFacility,
    drainListDtoToFacilities,
    mergeAnalysisIntoDetail,
    riskHistoryDtoToItems,
    sensorHistoryDtoToPoints,
    sortFacilitiesByRisk,
} from "@/lib/api/adapters";
import {
    getDashboardSummary,
    getDrainAnalysisHistory,
    getDrainDetail,
    getDrainRiskHistory,
    getDrainSensorHistory,
    getDrains,
    getLatestAnalysis,
} from "@/lib/api/drains";
import type {
    AnalysisResultDto,
    DashboardSummaryDto,
    DrainAnalysisHistoryResponse,
    DrainDetailDto,
    RiskHistoryDto,
    SensorHistoryDto,
} from "@/lib/api/types";
import type {
    DrainFacility,
    RiskHistoryItem,
    SensorPoint,
} from "@/lib/mock-data";

export type DashboardData = {
    drains: DrainFacility[];
    sortedDrains: DrainFacility[];
    summary: DashboardSummaryDto;
    source: "api";
};

export type DrainDetailData = {
    drain: DrainFacility;
    sensorHistory: SensorPoint[];
    riskHistory: RiskHistoryItem[];
    detail: DrainDetailDto;
    analysis?: AnalysisResultDto;
    analysisHistory?: DrainAnalysisHistoryResponse;
    source: "api";
};

export async function loadDashboardData(): Promise<DashboardData> {
    return tryLoadDashboardFromApi();
}

export async function loadDrainDetailData(
    id: string,
): Promise<DrainDetailData | null> {
    return tryLoadDrainDetailFromApi(id);
}

async function tryLoadDashboardFromApi(): Promise<DashboardData> {
    ensureApiBaseUrl();
    const [drainsResponse, summaryResponse] = await Promise.all([
            getDrains(),
            getDashboardSummary(),
    ]);

    const items = drainsResponse.data?.items;
    if (!drainsResponse.success || !items) throw new Error("Drain list request failed");

    const drains = drainListDtoToFacilities(items);
    return { drains, sortedDrains: sortFacilitiesByRisk(drains), summary: summaryResponse.success && summaryResponse.data ? summaryResponse.data : dashboardSummaryFromDrains(drains), source: "api" };
}

async function tryLoadDrainDetailFromApi(
    id: string,
): Promise<DrainDetailData | null> {
    ensureApiBaseUrl();
        const [
            detailResponse,
            sensorResponse,
            riskResponse,
            analysisResponse,
            historyResponse,
        ] = await Promise.all([
                getDrainDetail(id),
                getDrainSensorHistory(id, { range: "24h", limit: 48 }),
                getDrainRiskHistory(id, { days: 7, limit: 10 }),
                getLatestAnalysis(id),
                getDrainAnalysisHistory(id, { limit: 10 }).catch(() => null),
            ]);

        if (!detailResponse.success || !detailResponse.data) return null;

        return mapDetailResponses({
            detail: mergeAnalysisIntoDetail(
                detailResponse.data,
                analysisResponse.data,
            ),
            sensorHistory: sensorResponse.data?.items,
            riskHistory: riskResponse.data?.items,
            analysis: analysisResponse.data ?? undefined,
            analysisHistory:
                historyResponse?.success && historyResponse.data
                    ? historyResponse.data
                    : undefined,
            source: "api",
        });
}

function mapDetailResponses({
    detail,
    sensorHistory,
    riskHistory,
    analysis,
    analysisHistory,
    source,
}: {
    detail: DrainDetailDto;
    sensorHistory?: SensorHistoryDto[];
    riskHistory?: RiskHistoryDto[];
    analysis?: AnalysisResultDto;
    analysisHistory?: DrainAnalysisHistoryResponse;
    source: "api";
}): DrainDetailData {
    return {
        drain: drainDetailDtoToFacility(detail),
        sensorHistory: sensorHistoryDtoToPoints(
            sensorHistory ?? detail.sensorHistory ?? [],
        ),
        riskHistory: riskHistoryDtoToItems(
            riskHistory ?? detail.riskHistory ?? [],
        ),
        detail,
        analysis,
        analysisHistory,
        source,
    };
}

function ensureApiBaseUrl() {
    if (!process.env.NEXT_PUBLIC_API_BASE_URL) {
        throw new Error("NEXT_PUBLIC_API_BASE_URL is required");
    }
}
