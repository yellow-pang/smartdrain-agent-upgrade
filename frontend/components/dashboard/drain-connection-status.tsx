import type { DrainSocketStatus } from "@/lib/websocket/drain-status-socket";

export function DrainConnectionStatus({ status }: { status: DrainSocketStatus }) {
    return <span className="sr-only">{status}</span>;
}
