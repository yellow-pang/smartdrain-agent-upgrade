import { create } from "zustand";
import type { XgboostResultUpdatedEventDto, YoloResultUpdatedEventDto } from "@/lib/api/types";
import type { DrainSocketStatus } from "@/lib/websocket/drain-status-socket";

type DrainStore = {
    selectedDrainId: string | null;
    detailPanelOpen: boolean;
    socketStatus: DrainSocketStatus;
    lastMessageAt: string | null;
    lastError: string | null;
    yoloEventsByDrainId: Record<string, YoloResultUpdatedEventDto>;
    xgboostEventsByDrainId: Record<string, XgboostResultUpdatedEventDto>;
    selectDrain: (id: string | null) => void;
    setDetailPanelOpen: (open: boolean) => void;
    setSocketStatus: (status: DrainSocketStatus) => void;
    markMessageReceived: () => void;
    applyYoloEvent: (event: YoloResultUpdatedEventDto) => void;
    applyXgboostEvent: (event: XgboostResultUpdatedEventDto) => void;
};

export const useDrainStore = create<DrainStore>((set) => ({
    selectedDrainId: null,
    detailPanelOpen: false,
    socketStatus: "waiting",
    lastMessageAt: null,
    lastError: null,
    yoloEventsByDrainId: {},
    xgboostEventsByDrainId: {},
    selectDrain: (selectedDrainId) =>
        set({ selectedDrainId, detailPanelOpen: Boolean(selectedDrainId) }),
    setDetailPanelOpen: (detailPanelOpen) => set({ detailPanelOpen }),
    setSocketStatus: (socketStatus) =>
        set({
            socketStatus,
            lastError:
                socketStatus === "error" ? "실시간 연결에 실패했습니다." : null,
        }),
    markMessageReceived: () => set({ lastMessageAt: new Date().toISOString() }),
    applyYoloEvent: (event) => set((state) => ({ yoloEventsByDrainId: { ...state.yoloEventsByDrainId, [event.payload.drainId]: event } })),
    applyXgboostEvent: (event) => set((state) => ({ xgboostEventsByDrainId: { ...state.xgboostEventsByDrainId, [event.payload.drainId]: event } })),
}));
