"use client";

import { useCallback, useEffect } from "react";
import { useDrainStore } from "@/store/drain-store";
import { useDrainStatusSocket } from "@/lib/websocket/drain-status-socket";

export function RealtimeDrainSync() {
    const status = useDrainStore((state) => state.status);
    const initializeDashboard = useDrainStore((state) => state.initializeDashboard);
    const synchronizeDashboard = useDrainStore((state) => state.synchronizeDashboard);
    const applyStatusEvent = useDrainStore((state) => state.applyStatusEvent);
    const applyYoloEvent = useDrainStore((state) => state.applyYoloEvent);
    const applyXgboostEvent = useDrainStore((state) => state.applyXgboostEvent);
    const setSocketStatus = useDrainStore((state) => state.setSocketStatus);

    useEffect(() => {
        void initializeDashboard();
    }, [initializeDashboard]);

    const handleConnected = useCallback((reconnected: boolean) => {
        if (reconnected) void synchronizeDashboard();
    }, [synchronizeDashboard]);
    const socketStatus = useDrainStatusSocket({
        enabled: status === "success",
        onStatusUpdated: applyStatusEvent,
        onYoloUpdated: applyYoloEvent,
        onXgboostUpdated: applyXgboostEvent,
        onConnected: handleConnected,
    });

    useEffect(() => {
        setSocketStatus(socketStatus);
    }, [setSocketStatus, socketStatus]);

    return null;
}
