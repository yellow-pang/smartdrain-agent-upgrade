import { create } from "zustand";
import {
    dashboardSummaryFromDrains,
    mergeDrainStatusEventIntoFacility,
    sortFacilitiesByRisk,
} from "@/lib/api/adapters";
import { loadDashboardData, type DashboardData } from "@/lib/api/drain-data";
import type { DrainStatusUpdatedEventDto, XgboostResultUpdatedEventDto, YoloResultUpdatedEventDto } from "@/lib/api/types";
import type { DrainFacility } from "@/lib/mock-data";
import type { DrainSocketStatus } from "@/lib/websocket/drain-status-socket";

type DashboardLoadStatus = "loading" | "success" | "error";

type DrainStore = {
    dashboard: DashboardData | null;
    status: DashboardLoadStatus;
    errorMessage: string | null;
    selectedDrainId: string | null;
    socketStatus: DrainSocketStatus;
    lastSyncedAt: string | null;
    yoloEventsByDrainId: Record<string, YoloResultUpdatedEventDto>;
    xgboostEventsByDrainId: Record<string, XgboostResultUpdatedEventDto>;
    initializeDashboard: () => Promise<void>;
    synchronizeDashboard: () => Promise<void>;
    applyStatusEvent: (event: DrainStatusUpdatedEventDto) => void;
    applyYoloEvent: (event: YoloResultUpdatedEventDto) => void;
    applyXgboostEvent: (event: XgboostResultUpdatedEventDto) => void;
    selectDrain: (id: string | null) => void;
    setSocketStatus: (status: DrainSocketStatus) => void;
};

export const useDrainStore = create<DrainStore>((set, get) => ({
    dashboard: null,
    status: "loading",
    errorMessage: null,
    selectedDrainId: null,
    socketStatus: "waiting",
    lastSyncedAt: null,
    yoloEventsByDrainId: {},
    xgboostEventsByDrainId: {},
    initializeDashboard: async () => {
        set({ status: "loading", errorMessage: null });
        try {
            const dashboard = await loadDashboardData();
            set({
                dashboard,
                status: "success",
                selectedDrainId:
                    get().selectedDrainId ?? dashboard.sortedDrains[0]?.id ?? null,
                lastSyncedAt: new Date().toISOString(),
            });
        } catch {
            set({ status: "error", errorMessage: "시설 상태를 불러오지 못했습니다." });
        }
    },
    synchronizeDashboard: async () => {
        try {
            const next = await loadDashboardData();
            set((current) => ({
                dashboard: mergeDashboardData(current.dashboard, next),
                status: "success",
                errorMessage: null,
                lastSyncedAt: new Date().toISOString(),
            }));
        } catch {
            set({ errorMessage: "최신 상태 동기화에 실패했습니다." });
        }
    },
    applyStatusEvent: (event) => {
        set((current) => {
            if (!current.dashboard || !isNewer(event.payload.updatedAt, findDrain(current.dashboard, event.payload.drainId)?.updatedAt)) {
                return current;
            }
            const drains = current.dashboard.drains.map((drain) =>
                mergeDrainStatusEventIntoFacility(drain, event),
            );
            return {
                dashboard: {
                    ...current.dashboard,
                    drains,
                    sortedDrains: sortFacilitiesByRisk(drains),
                    summary: dashboardSummaryFromDrains(drains),
                },
            };
        });
    },
    applyYoloEvent: (event) => set((current) => {
        const previous = current.yoloEventsByDrainId[event.payload.drainId];
        return !previous || isNewer(event.payload.analyzedAt, previous.payload.analyzedAt)
            ? { yoloEventsByDrainId: { ...current.yoloEventsByDrainId, [event.payload.drainId]: event } }
            : current;
    }),
    applyXgboostEvent: (event) => set((current) => {
        const previous = current.xgboostEventsByDrainId[event.payload.drainId];
        return !previous || isNewer(event.payload.evaluatedAt, previous.payload.evaluatedAt)
            ? { xgboostEventsByDrainId: { ...current.xgboostEventsByDrainId, [event.payload.drainId]: event } }
            : current;
    }),
    selectDrain: (selectedDrainId) => set({ selectedDrainId }),
    setSocketStatus: (socketStatus) => set({ socketStatus }),
}));

function mergeDashboardData(current: DashboardData | null, next: DashboardData): DashboardData {
    if (!current) return next;
    const drains = next.drains.map((incoming) => {
        const existing = findDrain(current, incoming.id);
        return !existing || isNewer(incoming.updatedAt, existing.updatedAt)
            ? incoming
            : existing;
    });
    return { ...next, drains, sortedDrains: sortFacilitiesByRisk(drains), summary: dashboardSummaryFromDrains(drains) };
}

function findDrain(data: DashboardData, id: string): DrainFacility | undefined {
    return data.drains.find((drain) => drain.id === id);
}

function isNewer(candidate: string, current?: string): boolean {
    const candidateTime = Date.parse(candidate);
    if (Number.isNaN(candidateTime)) return false;
    if (!current) return true;
    const currentTime = Date.parse(current);
    return Number.isNaN(currentTime) || candidateTime > currentTime;
}
