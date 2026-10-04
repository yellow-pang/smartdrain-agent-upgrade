export const drainQueryKeys = {
    all: ["drains"] as const,
    detail: (drainId: string) => ["drains", drainId] as const,
    summary: ["dashboard", "summary"] as const,
    realtimeSimulatorStatus: ["realtime-simulator", "status"] as const,
};
