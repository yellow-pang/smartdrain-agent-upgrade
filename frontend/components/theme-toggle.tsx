"use client";

import { LaptopMinimal, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/components/theme-provider";

export function ThemeToggle() {
  const { mode, resolvedTheme, cycleMode } = useTheme();

  const meta =
    mode === "system"
      ? {
          icon: LaptopMinimal,
          label: `테마: 시스템 (${resolvedTheme === "dark" ? "다크" : "라이트"})`,
        }
      : mode === "dark"
        ? { icon: Moon, label: "테마: 다크" }
        : { icon: Sun, label: "테마: 라이트" };

  const Icon = meta.icon;

  return (
    <Button
      variant="ghost"
      size="icon"
      className="size-8 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 sm:size-9"
      aria-label={`${meta.label} · 클릭하여 변경`}
      title={`${meta.label} · 클릭하여 시스템/라이트/다크 순환`}
      onClick={cycleMode}
    >
      <Icon className="size-4 sm:size-5" />
    </Button>
  );
}
