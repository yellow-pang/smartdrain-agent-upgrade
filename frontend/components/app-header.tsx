"use client";

import { Bell, Droplet, Menu, User } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";

export function AppHeader({ notifications = 8 }: { notifications?: number }) {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-slate-200 bg-white px-3 sm:h-16 sm:px-4 md:px-6 dark:border-slate-800 dark:bg-slate-950/95">
      <div className="flex min-w-0 items-center gap-2 sm:gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          aria-label="메뉴 열기"
        >
          <Menu className="size-5" />
        </Button>
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
        <Button
          variant="ghost"
          size="icon"
          className="relative size-8 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 sm:size-9"
          aria-label="알림"
        >
          <Bell className="size-4 sm:size-5" />
          {notifications > 0 && (
            <span className="absolute right-1 top-1 flex min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
              {notifications}
            </span>
          )}
        </Button>
        <div className="mx-0.5 h-5 w-px bg-slate-200 dark:bg-slate-800 sm:mx-1 sm:h-6" />
        <Button
          variant="ghost"
          size="icon"
          className="size-8 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 sm:size-9"
          aria-label="사용자 메뉴"
        >
          <User className="size-4 sm:size-5" />
        </Button>
      </div>
    </header>
  );
}
