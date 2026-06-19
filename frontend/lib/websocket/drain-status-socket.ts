"use client";

import { useEffect, useRef, useState } from "react";
import type { DrainStatusUpdatedEventDto } from "@/lib/api/types";

export type DrainSocketStatus =
    | "waiting"
    | "connected"
    | "reconnecting"
    | "error";

const DRAIN_STATUS_SOCKET_PATH = "/ws/drains/status";
const RECONNECT_DELAY_MS = 3000;

type DrainRealtimeEvent = DrainStatusUpdatedEventDto;

export function useDrainStatusSocket({
    enabled,
    onStatusUpdated,
}: {
    enabled: boolean;
    onStatusUpdated: (event: DrainStatusUpdatedEventDto) => void;
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
                reconnectingRef.current = false;
                setStatus("connected");
            };

            socket.onmessage = (message) => {
                const event = parseDrainRealtimeEvent(message.data);
                if (!event) return;
                if (event.type === "DRAIN_STATUS_UPDATED") {
                    onStatusUpdated(event);
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
    }, [socketUrl, onStatusUpdated]);

    if (!enabled) return "waiting";
    if (!socketUrl) return "error";
    return status;
}

function parseDrainRealtimeEvent(data: string): DrainRealtimeEvent | null {
    try {
        const parsed = JSON.parse(data) as Partial<DrainRealtimeEvent>;
        if (parsed.type !== "DRAIN_STATUS_UPDATED") return null;
        if (!parsed.payload?.drainId || !parsed.payload.updatedAt) return null;
        return parsed as DrainStatusUpdatedEventDto;
    } catch {
        return null;
    }
}

function getDrainStatusSocketUrl() {
    const explicitUrl = process.env.NEXT_PUBLIC_WS_URL;
    if (explicitUrl) return withDrainStatusPath(explicitUrl);

    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (!apiBaseUrl) return null;

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
