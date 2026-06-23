"use client";

import { useCallback, useEffect, useMemo } from "react";
import { AppHeader } from "@/components/app-header";
import { DashboardMainContent } from "@/components/dashboard/dashboard-main-content";
import { DashboardSummarySection } from "@/components/dashboard/dashboard-summary-section";
import type {
    DrainRealtimeStatus,
    DrainRiskListStatus,
} from "@/components/dashboard/drain-risk-list";
import { sortFacilitiesByRisk } from "@/lib/api/adapters";
import {
    useDashboardSummaryQuery,
    useDrainsQuery,
} from "@/lib/query/drain-queries";
import type { DrainFacility } from "@/lib/mock-data";
import { useDrainStore } from "@/store/drain-store";

type DashboardData = {
    drains: DrainFacility[];
    sortedDrains: DrainFacility[];
};

export default function DashboardPage() {
    const drainsQuery = useDrainsQuery();
    const summaryQuery = useDashboardSummaryQuery();
    const { refetch: refetchDrains } = drainsQuery;
    const { refetch: refetchDashboardSummary } = summaryQuery;
    const selectedId = useDrainStore((state) => state.selectedDrainId);
    const selectDrain = useDrainStore((state) => state.selectDrain);
    const socketStatus = useDrainStore((state) => state.socketStatus);
    const handleSelectDrain = useCallback(
        (id: string) => {
            selectDrain(id);
        },
        [selectDrain],
    );
    const reloadDashboard = useCallback(() => {
        void refetchDrains();
        void refetchDashboardSummary();
    }, [refetchDashboardSummary, refetchDrains]);
    const dashboardData = useMemo<DashboardData | null>(() => {
        if (!drainsQuery.data) return null;

        return {
            drains: drainsQuery.data,
            sortedDrains: sortFacilitiesByRisk(drainsQuery.data),
        };
    }, [drainsQuery.data]);
    const sortedDrains = dashboardData?.sortedDrains ?? [];
    const effectiveSelectedId =
        selectedId && sortedDrains.some((drain) => drain.id === selectedId)
            ? selectedId
            : (sortedDrains[0]?.id ?? null);

    useEffect(() => {
        if (effectiveSelectedId !== selectedId) {
            selectDrain(effectiveSelectedId);
        }
    }, [effectiveSelectedId, selectedId, selectDrain]);

    const selectedDrain = useMemo(() => {
        if (!dashboardData || !effectiveSelectedId) return undefined;

        return dashboardData.drains.find((drain) => drain.id === effectiveSelectedId);
    }, [dashboardData, effectiveSelectedId]);
    const riskListStatus = getRiskListStatus(dashboardData, drainsQuery.isLoading);
    const riskListRealtimeStatus: DrainRealtimeStatus =
        riskListStatus === "error"
            ? "error"
            : riskListStatus === "loading"
                ? "waiting"
                : socketStatus;

    return (
        <div className="flex min-h-dvh flex-col bg-background">
            <AppHeader />
            <main className="mx-auto w-full max-w-[1600px] flex-1 p-4 md:p-6">
                <DashboardSummarySection
                    summary={summaryQuery.data}
                    isLoading={summaryQuery.isLoading}
                    onRetry={reloadDashboard}
                />
                <DashboardMainContent
                    mapDrains={dashboardData?.drains ?? []}
                    hasDashboardData={dashboardData !== null}
                    drains={sortedDrains}
                    selectedId={effectiveSelectedId}
                    selectedDrain={selectedDrain}
                    isLoading={drainsQuery.isLoading}
                    riskListStatus={riskListStatus}
                    realtimeStatus={riskListRealtimeStatus}
                    onSelectDrain={handleSelectDrain}
                    onRetry={reloadDashboard}
                />
            </main>
        </div>
    );
}

function getRiskListStatus(
    dashboardData: DashboardData | null,
    isLoading: boolean,
): DrainRiskListStatus {
    if (isLoading) return "loading";
    if (!dashboardData) return "error";
    if (dashboardData.sortedDrains.length === 0) return "empty";
    return "success";
}
