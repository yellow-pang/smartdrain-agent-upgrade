"use client";

import { useCallback, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { mergeDrainStatusEventIntoFacility } from "@/lib/api/adapters";
import { drainQueryKeys } from "@/lib/query/drain-query-keys";
import { useDrainsQuery } from "@/lib/query/drain-queries";
import type { DrainFacility } from "@/lib/mock-data";
import { useDrainStore } from "@/store/drain-store";
import { useDrainStatusSocket } from "@/lib/websocket/drain-status-socket";

export function RealtimeDrainSync() {
    const queryClient = useQueryClient();
    const { isSuccess } = useDrainsQuery();
    const applyYoloEvent = useDrainStore((state) => state.applyYoloEvent);
    const applyXgboostEvent = useDrainStore((state) => state.applyXgboostEvent);
    const setSocketStatus = useDrainStore((state) => state.setSocketStatus);
    const markMessageReceived = useDrainStore((state) => state.markMessageReceived);

    const applyStatusEvent = useCallback((event: Parameters<typeof mergeDrainStatusEventIntoFacility>[1]) => {
        queryClient.setQueryData<DrainFacility[]>(drainQueryKeys.all, (drains) =>
            drains?.map((drain) => mergeDrainStatusEventIntoFacility(drain, event)),
        );
        const detailKey = drainQueryKeys.detail(event.payload.drainId);
        if (queryClient.getQueryData(detailKey)) {
            queryClient.setQueryData(detailKey, (detail: { drain: DrainFacility } | null | undefined) =>
                detail ? { ...detail, drain: mergeDrainStatusEventIntoFacility(detail.drain, event) } : detail,
            );
        }
        markMessageReceived();
    }, [markMessageReceived, queryClient]);

    const handleConnected = useCallback((reconnected: boolean) => {
        if (!reconnected) return;
        void queryClient.invalidateQueries({ queryKey: drainQueryKeys.all });
        void queryClient.invalidateQueries({ queryKey: drainQueryKeys.summary });
        const selectedDrainId = useDrainStore.getState().selectedDrainId;
        if (useDrainStore.getState().detailPanelOpen && selectedDrainId) {
            void queryClient.invalidateQueries({ queryKey: drainQueryKeys.detail(selectedDrainId) });
        }
    }, [queryClient]);
    const socketStatus = useDrainStatusSocket({
        enabled: isSuccess,
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
