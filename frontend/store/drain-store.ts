import { create } from "zustand";
import type {
    DrainStatusUpdatedEventDto,
    XgboostResultUpdatedEventDto,
    YoloResultUpdatedEventDto,
} from "@/lib/api/types";
import { URGENT_ALERT_POLICY } from "@/lib/urgent-alert-policy";

export type UrgentDrainAlert = {
    drainId: string;
    facilityName?: string;
    message: string;
    updatedAt: string;
    read: boolean;
};
import type { DrainSocketStatus } from "@/lib/websocket/drain-status-socket";

type DrainStore = {
    selectedDrainId: string | null;
    detailPanelOpen: boolean;
    socketStatus: DrainSocketStatus;
    lastMessageAt: string | null;
    lastError: string | null;
    statusEventsByDrainId: Record<string, DrainStatusUpdatedEventDto>;
    yoloEventsByDrainId: Record<string, YoloResultUpdatedEventDto>;
    xgboostEventsByDrainId: Record<string, XgboostResultUpdatedEventDto>;
    urgentAlerts: UrgentDrainAlert[];
    selectDrain: (id: string | null) => void;
    setDetailPanelOpen: (open: boolean) => void;
    setSocketStatus: (status: DrainSocketStatus) => void;
    markMessageReceived: () => void;
    applyStatusEvent: (event: DrainStatusUpdatedEventDto) => void;
    applyYoloEvent: (event: YoloResultUpdatedEventDto) => void;
    applyXgboostEvent: (event: XgboostResultUpdatedEventDto) => void;
    upsertUrgentAlert: (
        event: DrainStatusUpdatedEventDto,
        facilityName?: string,
    ) => void;
    markUrgentAlertRead: (drainId: string) => void;
    markAllUrgentAlertsRead: () => void;
};

export const useDrainStore = create<DrainStore>((set) => ({
    selectedDrainId: null,
    detailPanelOpen: false,
    socketStatus: "waiting",
    lastMessageAt: null,
    lastError: null,
    statusEventsByDrainId: {},
    yoloEventsByDrainId: {},
    xgboostEventsByDrainId: {},
    urgentAlerts: [],
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
    applyStatusEvent: (event) =>
        set((state) => ({
            statusEventsByDrainId: {
                ...state.statusEventsByDrainId,
                [event.payload.drainId]: event,
            },
        })),
    applyYoloEvent: (event) => set((state) => ({ yoloEventsByDrainId: { ...state.yoloEventsByDrainId, [event.payload.drainId]: event } })),
    applyXgboostEvent: (event) => set((state) => ({ xgboostEventsByDrainId: { ...state.xgboostEventsByDrainId, [event.payload.drainId]: event } })),
    upsertUrgentAlert: (event, facilityName) =>
        set((state) => {
            const alert: UrgentDrainAlert = {
                drainId: event.payload.drainId,
                facilityName,
                message: event.payload.finalDecision ?? "즉시 현장 확인이 필요합니다.",
                updatedAt: event.payload.updatedAt,
                read: false,
            };
            const existingAlert = state.urgentAlerts.find(
                (item) => item.drainId === alert.drainId,
            );

            if (existingAlert) {
                return {
                    urgentAlerts: state.urgentAlerts.map((item) =>
                        item.drainId === alert.drainId ? { ...item, ...alert } : item,
                    ),
                };
            }

            return {
                urgentAlerts: [alert, ...state.urgentAlerts].slice(
                    0,
                    URGENT_ALERT_POLICY.maxVisibleAlerts,
                ),
            };
        }),
    markUrgentAlertRead: (drainId) =>
        set((state) => ({
            urgentAlerts: state.urgentAlerts.map((alert) =>
                alert.drainId === drainId ? { ...alert, read: true } : alert,
            ),
        })),
    markAllUrgentAlertsRead: () =>
        set((state) => ({
            urgentAlerts: state.urgentAlerts.map((alert) => ({
                ...alert,
                read: true,
            })),
        })),
}));
