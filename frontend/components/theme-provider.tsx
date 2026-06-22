"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

type ThemeMode = "system" | "light" | "dark";
type ResolvedTheme = "light" | "dark";

type ThemeContextValue = {
  mode: ThemeMode;
  resolvedTheme: ResolvedTheme;
  cycleMode: () => void;
  setMode: (mode: ThemeMode) => void;
};

const STORAGE_KEY = "smartdrain-theme-mode";

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(() => getInitialMode());
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>(() =>
    getInitialResolvedTheme(),
  );

  useEffect(() => {
    applyTheme(mode, setResolvedTheme);

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => {
      const currentMode = readStoredMode() ?? "system";
      if (currentMode === "system") {
        applyTheme("system", setResolvedTheme);
      }
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [mode]);

  const setMode = useCallback((nextMode: ThemeMode) => {
    persistMode(nextMode);
    setModeState(nextMode);
    applyTheme(nextMode, setResolvedTheme);
  }, []);

  const cycleMode = useCallback(() => {
    const nextMode =
      mode === "system" ? "light" : mode === "light" ? "dark" : "system";
    setMode(nextMode);
  }, [mode, setMode]);

  const value = useMemo(
    () => ({ mode, resolvedTheme, cycleMode, setMode }),
    [cycleMode, mode, resolvedTheme, setMode],
  );

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
}

function readStoredMode(): ThemeMode | null {
  if (typeof window === "undefined") return null;
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark" || stored === "system") {
    return stored;
  }
  return null;
}

function getInitialMode(): ThemeMode {
  if (typeof window === "undefined") return "system";
  return readStoredMode() ?? "system";
}

function getInitialResolvedTheme(): ResolvedTheme {
  if (typeof window === "undefined") return "light";

  const rootTheme = document.documentElement.classList.contains("dark")
    ? "dark"
    : document.documentElement.classList.contains("light")
      ? "light"
      : null;

  if (rootTheme) {
    return rootTheme;
  }

  return resolveTheme(readStoredMode() ?? "system");
}

function persistMode(mode: ThemeMode) {
  window.localStorage.setItem(STORAGE_KEY, mode);
}

function resolveTheme(mode: ThemeMode): ResolvedTheme {
  if (mode === "light" || mode === "dark") {
    return mode;
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function applyTheme(
  mode: ThemeMode,
  setResolvedTheme: (theme: ResolvedTheme) => void,
) {
  const nextResolvedTheme = resolveTheme(mode);
  const root = document.documentElement;

  root.classList.remove("light", "dark");
  root.classList.add(nextResolvedTheme);
  root.dataset.themeMode = mode;
  root.style.colorScheme = nextResolvedTheme;
  setResolvedTheme(nextResolvedTheme);
}
