import { apiClient } from "@/lib/api/client";
import type {
    ApiListResponse,
    ApiResponse,
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

export async function getDrainSensorHistory(id: string) {
    const response = await apiClient.get<ApiListResponse<SensorHistoryDto>>(
        `/api/drains/${id}/sensors`,
    );
    return response.data;
}

export async function getDrainRiskHistory(id: string) {
    const response = await apiClient.get<ApiListResponse<RiskHistoryDto>>(
        `/api/drains/${id}/risk-history`,
    );
    return response.data;
}
