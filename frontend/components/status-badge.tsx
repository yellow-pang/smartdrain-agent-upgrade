import { cn } from "@/lib/utils";
import { STATUS_META, type RiskStatus } from "@/lib/mock-data";

export function StatusBadge({
    status,
    className,
}: {
    status: RiskStatus;
    className?: string;
}) {
    const meta = STATUS_META[status];
    return (
        <span
            className={cn(
                "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-semibold",
                meta.badgeClass,
                className,
            )}
        >
            {meta.label}
        </span>
    );
}
