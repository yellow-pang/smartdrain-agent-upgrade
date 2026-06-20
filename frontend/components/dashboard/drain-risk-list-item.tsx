import { memo } from "react";
import type { DrainFacility } from "@/lib/mock-data";

export const DrainRiskListItem = memo(function DrainRiskListItem({ drain }: { drain: DrainFacility }) {
    return <span className="sr-only">{drain.id}</span>;
});
