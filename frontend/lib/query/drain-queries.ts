import { useQuery } from "@tanstack/react-query";
import {
    drainListDtoToFacilities,
} from "@/lib/api/adapters";
import { getDashboardSummary, getDrains } from "@/lib/api/drains";
import { loadDrainDetailData } from "@/lib/api/drain-data";
import { drainQueryKeys } from "@/lib/query/drain-query-keys";

const REALTIME_STALE_TIME = 30_000;

export async function fetchDrains() {
    const response = await getDrains();
    if (!response.success || !response.data) {
        throw new Error(response.error?.message ?? "시설 목록을 불러오지 못했습니다.");
    }
    return drainListDtoToFacilities(response.data.items);
}

export async function fetchDashboardSummary() {
    const response = await getDashboardSummary();
    if (!response.success || !response.data) {
        throw new Error(response.error?.message ?? "대시보드 요약을 불러오지 못했습니다.");
    }
    return response.data;
}

export function useDrainsQuery() {
    return useQuery({
        queryKey: drainQueryKeys.all,
        queryFn: fetchDrains,
        staleTime: REALTIME_STALE_TIME,
        refetchOnWindowFocus: false,
        retry: 1,
    });
}

export function useDashboardSummaryQuery() {
    return useQuery({
        queryKey: drainQueryKeys.summary,
        queryFn: fetchDashboardSummary,
        staleTime: REALTIME_STALE_TIME,
        refetchOnWindowFocus: false,
        retry: 1,
    });
}

export function useDrainDetailQuery(drainId: string) {
    return useQuery({
        queryKey: drainQueryKeys.detail(drainId),
        queryFn: () => loadDrainDetailData(drainId),
        staleTime: REALTIME_STALE_TIME,
        refetchOnWindowFocus: false,
        retry: 1,
    });
}
