"use client";

import { useEffect, useRef, useState } from "react";
import type {
    DrainRealtimeEventDto,
    DrainStatusUpdatedEventDto,
    XgboostResultUpdatedEventDto,
    YoloResultUpdatedEventDto,
} from "@/lib/api/types";

export type DrainSocketStatus =
    | "waiting"
    | "connected"
    | "reconnecting"
    | "error";

const DRAIN_STATUS_SOCKET_PATH = "/ws/drains/status";
const RECONNECT_DELAY_MS = 3000;

export function useDrainStatusSocket({
    enabled,
    onStatusUpdated,
    onYoloUpdated,
    onXgboostUpdated,
    onConnected,
}: {
    enabled: boolean;
    onStatusUpdated: (event: DrainStatusUpdatedEventDto) => void;
    onYoloUpdated?: (event: YoloResultUpdatedEventDto) => void;
    onXgboostUpdated?: (event: XgboostResultUpdatedEventDto) => void;
    onConnected?: (reconnected: boolean) => void;
}) {
    const [status, setStatus] = useState<DrainSocketStatus>("waiting");
    const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(
        null,
    );
    const reconnectingRef = useRef(false);
    const socketUrl = enabled ? getDrainStatusSocketUrl() : null;

    useEffect(() => {
        if (!socketUrl) {
            return;
        }

        let socket: WebSocket | null = null;
        let disposed = false;

        const clearReconnectTimer = () => {
            if (!reconnectTimerRef.current) return;
            clearTimeout(reconnectTimerRef.current);
            reconnectTimerRef.current = null;
        };

        const connect = () => {
            socket = new WebSocket(socketUrl);
            setStatus(reconnectingRef.current ? "reconnecting" : "waiting");

            socket.onopen = () => {
                const reconnected = reconnectingRef.current;
                reconnectingRef.current = false;
                setStatus("connected");
                onConnected?.(reconnected);
            };

            socket.onmessage = (message) => {
                const event = parseDrainRealtimeEvent(message.data);
                if (!event) return;
                if (event.type === "DRAIN_STATUS_UPDATED") {
                    onStatusUpdated(event);
                    return;
                }
                if (event.type === "YOLO_RESULT_UPDATED") {
                    onYoloUpdated?.(event);
                    return;
                }
                if (event.type === "XGBOOST_RESULT_UPDATED") {
                    onXgboostUpdated?.(event);
                }
            };

            socket.onerror = () => {
                setStatus("error");
            };

            socket.onclose = () => {
                if (disposed) return;
                reconnectingRef.current = true;
                setStatus("reconnecting");
                clearReconnectTimer();
                reconnectTimerRef.current = setTimeout(
                    connect,
                    RECONNECT_DELAY_MS,
                );
            };
        };

        connect();

        return () => {
            disposed = true;
            reconnectingRef.current = false;
            clearReconnectTimer();
            socket?.close();
        };
    }, [socketUrl, onStatusUpdated, onYoloUpdated, onXgboostUpdated, onConnected]);

    if (!enabled) return "waiting";
    if (!socketUrl) return "error";
    return status;
}

function parseDrainRealtimeEvent(data: string): DrainRealtimeEventDto | null {
    try {
        const parsed = JSON.parse(data) as Partial<DrainRealtimeEventDto>;
        if (!parsed.payload?.drainId) return null;

        if (parsed.type === "DRAIN_STATUS_UPDATED") {
            if (!parsed.payload.updatedAt) return null;
            return parsed as DrainStatusUpdatedEventDto;
        }

        if (parsed.type === "YOLO_RESULT_UPDATED") {
            const payload = parsed.payload as Partial<
                YoloResultUpdatedEventDto["payload"]
            >;
            if (!payload.updatedAt || !payload.analyzedAt) return null;
            return parsed as YoloResultUpdatedEventDto;
        }

        if (parsed.type === "XGBOOST_RESULT_UPDATED") {
            const payload = parsed.payload as Partial<
                XgboostResultUpdatedEventDto["payload"]
            >;
            if (!payload.updatedAt || !payload.evaluatedAt) return null;
            return parsed as XgboostResultUpdatedEventDto;
        }

        return null;
    } catch {
        return null;
    }
}

function getDrainStatusSocketUrl() {
    const explicitUrl = process.env.NEXT_PUBLIC_WS_URL;
    if (explicitUrl) return withDrainStatusPath(explicitUrl);

    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (!apiBaseUrl) return null;

    if (apiBaseUrl.startsWith("/")) {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        return `${protocol}//${window.location.host}${DRAIN_STATUS_SOCKET_PATH}`;
    }

    return withDrainStatusPath(
        apiBaseUrl
            .replace(/^http:\/\//, "ws://")
            .replace(/^https:\/\//, "wss://"),
    );
}

function withDrainStatusPath(url: string) {
    if (url.includes(DRAIN_STATUS_SOCKET_PATH)) return url;
    return `${url.replace(/\/$/, "")}${DRAIN_STATUS_SOCKET_PATH}`;
}
