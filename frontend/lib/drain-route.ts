export function getDrainDetailHref(drainId: string) {
    return `/drains/${encodeURIComponent(drainId.trim())}`;
}
