import { apiClient } from "@/lib/api/client";
import type {
    ApiListResponse,
    ApiResponse,
    AnalysisResultDto,
    DashboardSummaryDto,
    DrainAnalysisHistoryResponse,
    DrainDetailDto,
    DrainListItemDto,
    RiskHistoryDto,
    SensorHistoryDto,
} from "@/lib/api/types";

export async function getDrains() {
    const response =
        await apiClient.get<ApiListResponse<DrainListItemDto>>("/api/drains");
    return response.data;
}

export async function getDrainDetail(id: string) {
    const response = await apiClient.get<ApiResponse<DrainDetailDto>>(
        `/api/drains/${id}`,
    );
    return response.data;
}

export async function getDrainSensorHistory(
    id: string,
    params?: { range?: string; limit?: number },
) {
    const response = await apiClient.get<ApiListResponse<SensorHistoryDto>>(
        `/api/drains/${id}/sensors`,
        { params },
    );
    return response.data;
}

export async function getDrainRiskHistory(
    id: string,
    params?: { days?: number; limit?: number },
) {
    const response = await apiClient.get<ApiListResponse<RiskHistoryDto>>(
        `/api/drains/${id}/risk-history`,
        { params },
    );
    return response.data;
}

export async function getDashboardSummary() {
    const response = await apiClient.get<ApiResponse<DashboardSummaryDto>>(
        "/api/dashboard/summary",
    );
    return response.data;
}

export async function getLatestAnalysis(id: string) {
    const response = await apiClient.get<ApiResponse<AnalysisResultDto>>(
        `/api/drains/${id}/analysis/latest`,
    );
    return response.data;
}

export async function getDrainAnalysisHistory(
    id: string,
    params?: { limit?: number },
) {
    const response = await apiClient.get<
        ApiResponse<DrainAnalysisHistoryResponse>
    >(`/api/drains/${id}/analysis/history`, { params });
    return response.data;
}
