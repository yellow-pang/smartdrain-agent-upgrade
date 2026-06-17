import { cn } from "@/lib/utils"

// A thin progress bar coloured by status, with optional value + label on the right.
export function MetricProgress({
  value,
  barClass,
  className,
  trackClass,
}: {
  value: number // 0-100
  barClass: string
  className?: string
  trackClass?: string
}) {
  return (
    <div className={cn("h-2 w-full overflow-hidden rounded-full bg-slate-100", trackClass, className)}>
      <div
        className={cn("h-full rounded-full transition-all duration-500", barClass)}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  )
}
