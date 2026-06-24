import { Badge } from "@/components/ui/badge";

export function PlaceholderState({
    image,
    title,
    description,
    statusLabel,
    className = "min-h-[420px]",
}: {
    image: string;
    title: string;
    description: string;
    statusLabel: string;
    className?: string;
}) {
    return (
        <div
            className={`relative flex overflow-hidden rounded-xl border border-dashed border-slate-200 bg-slate-50 ${className}`}
        >
            <div
                className="absolute inset-0 bg-contain bg-center bg-no-repeat opacity-95"
                style={{ backgroundImage: `url(${image})` }}
                aria-hidden="true"
            />
            <div className="absolute inset-0 bg-white/30" />
            <div className="relative z-10 mt-auto w-full bg-white/85 px-4 py-3 backdrop-blur-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                        <p className="text-sm font-bold text-slate-800">
                            {title}
                        </p>
                        <p className="mt-0.5 text-xs text-slate-500">
                            {description}
                        </p>
                    </div>
                    <Badge className="border-slate-200 bg-slate-100 text-slate-600">
                        {statusLabel}
                    </Badge>
                </div>
            </div>
        </div>
    );
}
