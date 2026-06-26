"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { AlertTriangle, Bell, Droplet, Menu, User } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { ComingSoonPopover } from "@/components/coming-soon-popover";
import { Button } from "@/components/ui/button";
import { formatDateTimeForDisplay } from "@/lib/date-format";
import { getDrainDetailHref } from "@/lib/drain-route";
import { STATUS_META } from "@/lib/risk";
import { useDrainStore } from "@/store/drain-store";

export function AppHeader() {
  const [isAlertOpen, setIsAlertOpen] = useState(false);
  const [comingSoonTarget, setComingSoonTarget] = useState<
    "menu" | "user" | null
  >(null);
  const urgentAlerts = useDrainStore((state) => state.urgentAlerts);
  const markUrgentAlertRead = useDrainStore(
    (state) => state.markUrgentAlertRead,
  );
  const markAllUrgentAlertsRead = useDrainStore(
    (state) => state.markAllUrgentAlertsRead,
  );
  const unreadCount = urgentAlerts.filter((alert) => !alert.read).length;
  const unreadDangerCount = urgentAlerts.filter(
    (alert) => !alert.read && alert.riskLevel === "danger",
  ).length;
  const unreadUnknownCount = urgentAlerts.filter(
    (alert) => !alert.read && alert.riskLevel === "unknown",
  ).length;
  const closeComingSoon = useCallback(() => setComingSoonTarget(null), []);

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-slate-200 bg-white px-3 sm:h-16 sm:px-4 md:px-6 dark:border-slate-800 dark:bg-slate-950/95">
      <div className="flex min-w-0 items-center gap-2 sm:gap-3">
        <div className="relative">
          <Button
            variant="ghost"
            size="icon"
            className="text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
            aria-label="메뉴 열기"
            aria-expanded={comingSoonTarget === "menu"}
            onClick={() => {
              setIsAlertOpen(false);
              setComingSoonTarget("menu");
            }}
          >
            <Menu className="size-5" />
          </Button>
          {comingSoonTarget === "menu" && (
            <ComingSoonPopover
              message="메뉴 기능은 준비 중입니다."
              onClose={closeComingSoon}
            />
          )}
        </div>
        <div className="flex min-w-0 items-center gap-2 sm:gap-2.5">
          <span className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-cyan-600 text-white sm:size-8">
            <Droplet className="size-4 sm:size-5" fill="currentColor" />
          </span>
          <h1 className="min-w-0 truncate font-bold tracking-tight text-slate-900 dark:text-slate-100">
            <span className="block text-sm sm:hidden">침수 관리 대시보드</span>
            <span className="hidden text-base sm:block md:text-lg">
              지능형 도시 침수 관리 대시보드
            </span>
          </h1>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-0.5 sm:gap-1">
        <ThemeToggle />
        <div className="relative">
          <Button
            variant="ghost"
            size="icon"
            className="relative size-8 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 sm:size-9"
            aria-label={unreadCount > 0 ? `긴급 알림 ${unreadCount}건` : "알림"}
            aria-expanded={isAlertOpen}
            onClick={() => setIsAlertOpen((open) => !open)}
          >
            <Bell className="size-4 sm:size-5" />
            {unreadCount > 0 && (
              <span className="absolute right-1 top-1 flex min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
                {unreadCount}
              </span>
            )}
          </Button>
          {isAlertOpen && (
            <section
              className="fixed left-3 right-3 top-16 z-50 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl sm:absolute sm:left-auto sm:right-0 sm:top-10 sm:w-[22rem] dark:border-slate-700 dark:bg-slate-900"
              aria-label="긴급 알림 목록"
            >
              <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3 dark:border-slate-800">
                <div>
                  <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                    긴급 알림
                  </h2>
                  <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                    시설별 한 건으로 최신 위험·판단불가 상태를 갱신합니다.
                  </p>
                </div>
                {unreadCount > 0 && (
                  <button
                    type="button"
                    className="text-xs font-semibold text-cyan-700 hover:text-cyan-800 dark:text-cyan-400 dark:hover:text-cyan-300"
                    onClick={markAllUrgentAlertsRead}
                  >
                    모두 읽음
                  </button>
                )}
              </div>
              {urgentAlerts.length > 0 && (
                <div className="grid grid-cols-2 gap-2 border-b border-slate-100 px-3 py-2 dark:border-slate-800">
                  <AlertSummary label="읽지 않은 위험" count={unreadDangerCount} tone="danger" />
                  <AlertSummary label="판단불가" count={unreadUnknownCount} tone="unknown" />
                </div>
              )}
              {urgentAlerts.length > 0 ? (
                <ul className="dashboard-scrollbar max-h-80 overflow-y-auto p-2">
                  {urgentAlerts.map((alert) => (
                    <li key={alert.drainId}>
                      <Link
                        href={getDrainDetailHref(alert.drainId)}
                        className="block rounded-lg px-3 py-3 hover:bg-red-50 dark:hover:bg-red-950/30"
                        onClick={() => {
                          markUrgentAlertRead(alert.drainId);
                          setIsAlertOpen(false);
                        }}
                      >
                        <div className="flex items-start gap-2">
                          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-red-500" />
                          <div className="min-w-0 flex-1">
                            <div className="flex flex-wrap items-center gap-1.5">
                              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                                {alert.facilityName ?? alert.drainId}
                              </p>
                              <span className={`rounded-full border px-1.5 py-0.5 text-[10px] font-semibold ${STATUS_META[alert.riskLevel].badgeClass}`}>
                                {STATUS_META[alert.riskLevel].label}
                              </span>
                            </div>
                            <p className="mt-0.5 break-words text-xs text-slate-600 dark:text-slate-300">
                              {alert.message}
                            </p>
                            <p className="mt-1 text-[11px] text-slate-400 dark:text-slate-500">
                              {formatDateTimeForDisplay(alert.updatedAt)}
                            </p>
                          </div>
                          {!alert.read && (
                            <span className="mt-1 size-2 shrink-0 rounded-full bg-red-500" aria-label="읽지 않음" />
                          )}
                        </div>
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="px-4 py-8 text-center text-sm text-slate-500 dark:text-slate-400">
                  새 긴급 알림이 없습니다.
                </p>
              )}
            </section>
          )}
        </div>
        <div className="mx-0.5 h-5 w-px bg-slate-200 dark:bg-slate-800 sm:mx-1 sm:h-6" />
        <div className="relative">
          <Button
            variant="ghost"
            size="icon"
            className="size-8 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 sm:size-9"
            aria-label="사용자 메뉴"
            aria-expanded={comingSoonTarget === "user"}
            onClick={() => {
              setIsAlertOpen(false);
              setComingSoonTarget("user");
            }}
          >
            <User className="size-4 sm:size-5" />
          </Button>
          {comingSoonTarget === "user" && (
            <ComingSoonPopover
              message="사용자 기능은 준비 중입니다."
              onClose={closeComingSoon}
              align="end"
            />
          )}
        </div>
      </div>
    </header>
  );
}

function AlertSummary({
  label,
  count,
  tone,
}: {
  label: string;
  count: number;
  tone: "danger" | "unknown";
}) {
  const toneClass =
    tone === "danger"
      ? "border-red-100 bg-red-50 text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300"
      : "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200";

  return (
    <div className={`rounded-lg border px-3 py-2 ${toneClass}`}>
      <p className="text-[11px] font-medium">{label}</p>
      <p className="mt-0.5 text-lg font-bold leading-none">{count}</p>
    </div>
  );
}
