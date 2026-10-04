import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, PauseCircle, PlayCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDateTimeForDisplay } from "@/lib/date-format";
import { startRealtimeSimulator, stopRealtimeSimulator } from "@/lib/api/drains";
import { drainQueryKeys } from "@/lib/query/drain-query-keys";
import { useRealtimeSimulatorStatusQuery } from "@/lib/query/drain-queries";

const DEFAULT_SIMULATOR_INTERVAL_SECONDS = 20;

export function RealtimeSimulatorControl() {
    const queryClient = useQueryClient();
    const statusQuery = useRealtimeSimulatorStatusQuery();
    const status = statusQuery.data;

    const startMutation = useMutation({
        mutationFn: () => startRealtimeSimulator(DEFAULT_SIMULATOR_INTERVAL_SECONDS),
        onSuccess: async () => {
            await queryClient.invalidateQueries({
                queryKey: drainQueryKeys.realtimeSimulatorStatus,
            });
        },
    });
    const stopMutation = useMutation({
        mutationFn: stopRealtimeSimulator,
        onSuccess: async () => {
            await queryClient.invalidateQueries({
                queryKey: drainQueryKeys.realtimeSimulatorStatus,
            });
        },
    });

    const isPending = startMutation.isPending || stopMutation.isPending;
    const errorMessage =
        statusQuery.error instanceof Error
            ? statusQuery.error.message
            : startMutation.error instanceof Error
                ? startMutation.error.message
                : stopMutation.error instanceof Error
                    ? stopMutation.error.message
                    : null;

    return (
        <section className="mb-4 rounded-xl border border-slate-200 bg-white px-4 py-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 md:px-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-1">
                    <div className="flex items-center gap-2">
                        <p className="text-sm font-bold text-slate-900 dark:text-slate-100">
                            자동 시뮬레이터
                        </p>
                        <Badge
                            variant={status?.running ? "default" : "outline"}
                            className={
                                status?.running
                                    ? "bg-emerald-600 text-white"
                                    : "text-slate-600 dark:text-slate-300"
                            }
                        >
                            {status?.running ? "실행 중" : "중지됨"}
                        </Badge>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                        수동 분석 방식은 유지하고 자동 주기 실행({DEFAULT_SIMULATOR_INTERVAL_SECONDS}초)을 추가합니다.
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        size="sm"
                        variant="outline"
                        disabled={isPending || status?.running === true}
                        onClick={() => startMutation.mutate()}
                    >
                        {startMutation.isPending ? <Loader2 className="size-3.5 animate-spin" /> : <PlayCircle className="size-3.5" />}
                        시작
                    </Button>
                    <Button
                        size="sm"
                        variant="outline"
                        disabled={isPending || status?.running === false}
                        onClick={() => stopMutation.mutate()}
                    >
                        {stopMutation.isPending ? <Loader2 className="size-3.5 animate-spin" /> : <PauseCircle className="size-3.5" />}
                        중지
                    </Button>
                </div>
            </div>
            <div className="mt-3 grid gap-2 text-xs text-slate-600 dark:text-slate-300 md:grid-cols-3">
                <p>
                    최근 실행: {status?.lastTickAt ? formatDateTimeForDisplay(status.lastTickAt) : "-"}
                </p>
                <p>최근 실행 drain 수: {status?.lastRunDrainCount ?? 0}</p>
                <p>누적 실행 횟수: {status?.totalRunCount ?? 0}</p>
            </div>
            {status?.lastError ? (
                <p className="mt-2 text-xs text-red-600 dark:text-red-300">
                    최근 오류: {status.lastError}
                </p>
            ) : null}
            {errorMessage ? (
                <p className="mt-2 text-xs text-red-600 dark:text-red-300">
                    상태 확인 오류: {errorMessage}
                </p>
            ) : null}
        </section>
    );
}
