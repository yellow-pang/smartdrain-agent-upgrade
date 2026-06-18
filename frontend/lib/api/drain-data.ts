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
    getDrainDetail,
    getDrainRiskHistory,
    getDrainSensorHistory,
    getDrains,
    getLatestAnalysis,
} from "@/lib/api/drains";
import {
    createMockDashboardSummaryResponse,
    createMockDrainDetailResponse,
    createMockDrainListResponse,
    createMockLatestAnalysisResponse,
    createMockRiskHistoryResponse,
    createMockSensorHistoryResponse,
} from "@/lib/api/mock-responses";
import type {
    AnalysisResultDto,
    DashboardSummaryDto,
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
    source: "api" | "mock";
};

export type DrainDetailData = {
    drain: DrainFacility;
    sensorHistory: SensorPoint[];
    riskHistory: RiskHistoryItem[];
    detail: DrainDetailDto;
    analysis?: AnalysisResultDto;
    source: "api" | "mock";
};

export async function loadDashboardData(): Promise<DashboardData> {
    const apiData = await tryLoadDashboardFromApi();
    if (apiData) return apiData;
    return loadDashboardFromMock();
}

export async function loadDrainDetailData(
    id: string,
): Promise<DrainDetailData | null> {
    const apiData = await tryLoadDrainDetailFromApi(id);
    if (apiData) return apiData;
    return loadDrainDetailFromMock(id);
}

async function tryLoadDashboardFromApi(): Promise<DashboardData | null> {
    if (!hasApiBaseUrl()) return null;

    try {
        const [drainsResponse, summaryResponse] = await Promise.all([
            getDrains(),
            getDashboardSummary(),
        ]);

        const items = drainsResponse.data?.items;
        if (!drainsResponse.success || !items) return null;

        const drains = drainListDtoToFacilities(items);
        return {
            drains,
            sortedDrains: sortFacilitiesByRisk(drains),
            summary:
                summaryResponse.success && summaryResponse.data
                    ? summaryResponse.data
                    : dashboardSummaryFromDrains(drains),
            source: "api",
        };
    } catch {
        return null;
    }
}

async function tryLoadDrainDetailFromApi(
    id: string,
): Promise<DrainDetailData | null> {
    if (!hasApiBaseUrl()) return null;

    try {
        const [detailResponse, sensorResponse, riskResponse, analysisResponse] =
            await Promise.all([
                getDrainDetail(id),
                getDrainSensorHistory(id, { range: "24h", limit: 48 }),
                getDrainRiskHistory(id, { days: 7, limit: 10 }),
                getLatestAnalysis(id),
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
            source: "api",
        });
    } catch {
        return null;
    }
}

function loadDashboardFromMock(): DashboardData {
    const response = createMockDrainListResponse();
    const drains = drainListDtoToFacilities(response.data?.items ?? []);
    const summaryResponse = createMockDashboardSummaryResponse();
    return {
        drains,
        sortedDrains: sortFacilitiesByRisk(drains),
        summary: summaryResponse.data ?? dashboardSummaryFromDrains(drains),
        source: "mock",
    };
}

function loadDrainDetailFromMock(id: string): DrainDetailData | null {
    const detailResponse = createMockDrainDetailResponse(id);
    if (!detailResponse.success || !detailResponse.data) return null;

    const sensorResponse = createMockSensorHistoryResponse(id);
    const riskResponse = createMockRiskHistoryResponse(id);
    const analysisResponse = createMockLatestAnalysisResponse(id);

    return mapDetailResponses({
        detail: mergeAnalysisIntoDetail(
            detailResponse.data,
            analysisResponse.data,
        ),
        sensorHistory: sensorResponse.data?.items,
        riskHistory: riskResponse.data?.items,
        analysis: analysisResponse.data ?? undefined,
        source: "mock",
    });
}

function mapDetailResponses({
    detail,
    sensorHistory,
    riskHistory,
    analysis,
    source,
}: {
    detail: DrainDetailDto;
    sensorHistory?: SensorHistoryDto[];
    riskHistory?: RiskHistoryDto[];
    analysis?: AnalysisResultDto;
    source: "api" | "mock";
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
        source,
    };
}

function hasApiBaseUrl() {
    return Boolean(process.env.NEXT_PUBLIC_API_BASE_URL);
}
