"use client";

import { Bell, Droplet, Menu, User } from "lucide-react";
import { Button } from "@/components/ui/button";

export function AppHeader({ notifications = 8 }: { notifications?: number }) {
    return (
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 md:px-6">
            <div className="flex items-center gap-3">
                <Button
                    variant="ghost"
                    size="icon"
                    className="text-slate-600 hover:bg-slate-100"
                    aria-label="메뉴 열기"
                >
                    <Menu className="size-5" />
                </Button>
                <div className="flex items-center gap-2.5">
                    <span className="flex size-8 items-center justify-center rounded-lg bg-cyan-600 text-white">
                        <Droplet className="size-5" fill="currentColor" />
                    </span>
                    <h1 className="text-balance text-base font-bold tracking-tight text-slate-900 md:text-lg">
                        지능형 도시 침수 관리 대시보드
                    </h1>
                </div>
            </div>

            <div className="flex items-center gap-1">
                <Button
                    variant="ghost"
                    size="icon"
                    className="relative text-slate-600 hover:bg-slate-100"
                    aria-label="알림"
                >
                    <Bell className="size-5" />
                    {notifications > 0 && (
                        <span className="absolute right-1 top-1 flex min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
                            {notifications}
                        </span>
                    )}
                </Button>
                <div className="mx-1 h-6 w-px bg-slate-200" />
                <Button
                    variant="ghost"
                    size="icon"
                    className="text-slate-600 hover:bg-slate-100"
                    aria-label="사용자 메뉴"
                >
                    <User className="size-5" />
                </Button>
            </div>
        </header>
    );
}
