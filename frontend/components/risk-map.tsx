"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, Crosshair, Minus, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { DRAINS, STATUS_META, type DrainFacility } from "@/lib/mock-data";
import type { RiskLevel } from "@/lib/risk";

type KakaoSdkStatus = "idle" | "loading" | "ready" | "error";

type KakaoLatLng = {
    getLat(): number;
    getLng(): number;
};

type KakaoMap = {
    setCenter(position: KakaoLatLng): void;
    addControl(control: unknown, position: number): void;
};

type KakaoMarker = {
    setMap(map: KakaoMap | null): void;
};

type KakaoCustomOverlay = {
    setMap(map: KakaoMap | null): void;
};

type KakaoEventTarget = KakaoMarker;

type KakaoMaps = {
    load(callback: () => void): void;
    LatLng: new (lat: number, lng: number) => KakaoLatLng;
    LatLngBounds: new () => {
        extend(position: KakaoLatLng): void;
    };
    Map: new (
        container: HTMLElement,
        options: {
            center: KakaoLatLng;
            level: number;
        },
    ) => KakaoMap;
    Marker: new (options: {
        position: KakaoLatLng;
        image: unknown;
        title: string;
    }) => KakaoMarker;
    MarkerImage: new (
        src: string,
        size: unknown,
        options: {
            offset: unknown;
        },
    ) => unknown;
    Size: new (width: number, height: number) => unknown;
    Point: new (x: number, y: number) => unknown;
    CustomOverlay: new (options: {
        position: KakaoLatLng;
        content: string;
        yAnchor: number;
        zIndex: number;
    }) => KakaoCustomOverlay;
    ZoomControl: new () => unknown;
    ControlPosition: {
        RIGHT: number;
    };
    event: {
        addListener(
            target: KakaoEventTarget,
            type: "click",
            callback: () => void,
        ): void;
    };
};

declare global {
    interface Window {
        kakao?: {
            maps: KakaoMaps;
        };
    }
}

const KAKAO_SDK_ID = "kakao-map-sdk";
const DEFAULT_CENTER = {
    latitude: 37.4979,
    longitude: 127.0276,
};

const MARKER_COLORS: Record<RiskLevel, string> = {
    danger: "#ef4444",
    caution: "#f59e0b",
    good: "#10b981",
    unknown: "#94a3b8",
};

let kakaoSdkPromise: Promise<void> | null = null;

export function RiskMap({
    drains = DRAINS,
    selectedId,
    onSelect,
    labelLocation,
}: {
    drains?: DrainFacility[];
    selectedId?: string | null;
    onSelect?: (id: string) => void;
    labelLocation?: string;
}) {
    const containerRef = useRef<HTMLDivElement | null>(null);
    const mapRef = useRef<KakaoMap | null>(null);
    const markerRefs = useRef<KakaoMarker[]>([]);
    const overlayRef = useRef<KakaoCustomOverlay | null>(null);
    const [sdkStatus, setSdkStatus] = useState<KakaoSdkStatus>("idle");
    const appKey = process.env.NEXT_PUBLIC_KAKAO_MAP_APP_KEY;
    const validDrains = useMemo(() => drains.filter(hasValidCoordinate), [
        drains,
    ]);
    const selectedDrain = useMemo(
        () => validDrains.find((drain) => drain.id === selectedId),
        [selectedId, validDrains],
    );
    const mapDisplayStatus =
        sdkStatus === "idle" && appKey && validDrains.length > 0
            ? "loading"
            : sdkStatus;
    const shouldUseFallback =
        !appKey || sdkStatus === "error" || validDrains.length === 0;

    useEffect(() => {
        if (!appKey || validDrains.length === 0) return;

        loadKakaoMapsSdk(appKey)
            .then(() => setSdkStatus("ready"))
            .catch(() => setSdkStatus("error"));
    }, [appKey, validDrains.length]);

    useEffect(() => {
        if (sdkStatus !== "ready" || !containerRef.current || !window.kakao) {
            return;
        }

        const kakao = window.kakao;
        const center = getMapCenter(validDrains);
        const map = new kakao.maps.Map(containerRef.current, {
            center: new kakao.maps.LatLng(center.latitude, center.longitude),
            level: validDrains.length > 1 ? 5 : 3,
        });

        map.addControl(
            new kakao.maps.ZoomControl(),
            kakao.maps.ControlPosition.RIGHT,
        );
        mapRef.current = map;

        return () => {
            clearKakaoMarkers();
            mapRef.current = null;
        };
    }, [sdkStatus, validDrains]);

    useEffect(() => {
        if (sdkStatus !== "ready" || !mapRef.current || !window.kakao) return;

        const kakao = window.kakao;
        clearKakaoMarkers();

        markerRefs.current = validDrains.map((drain) => {
            const marker = new kakao.maps.Marker({
                position: new kakao.maps.LatLng(drain.latitude, drain.longitude),
                image: new kakao.maps.MarkerImage(
                    createMarkerImage(drain.status, drain.id === selectedId),
                    new kakao.maps.Size(34, 44),
                    {
                        offset: new kakao.maps.Point(17, 42),
                    },
                ),
                title: `${drain.id} ${drain.road}`,
            });

            marker.setMap(mapRef.current);
            kakao.maps.event.addListener(marker, "click", () => {
                onSelect?.(drain.id);
            });
            return marker;
        });

        if (selectedDrain) {
            const selectedPosition = new kakao.maps.LatLng(
                selectedDrain.latitude,
                selectedDrain.longitude,
            );
            mapRef.current.setCenter(selectedPosition);
            overlayRef.current = new kakao.maps.CustomOverlay({
                position: selectedPosition,
                content: createSelectedOverlayContent(
                    labelLocation ?? selectedDrain.road,
                ),
                yAnchor: 2.1,
                zIndex: 20,
            });
            overlayRef.current.setMap(mapRef.current);
        }

        return clearKakaoMarkers;
    }, [labelLocation, onSelect, sdkStatus, selectedDrain, selectedId, validDrains]);

    const legendCounts = {
        danger: drains.filter((drain) => drain.status === "danger").length,
        caution: drains.filter((drain) => drain.status === "caution").length,
        good: drains.filter((drain) => drain.status === "good").length,
        unknown: drains.filter((drain) => drain.status === "unknown").length,
    };

    return (
        <div className="relative h-full min-h-[420px] w-full overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
            {shouldUseFallback ? (
                <FallbackRiskMap
                    drains={drains}
                    selectedId={selectedId}
                    onSelect={onSelect}
                    labelLocation={labelLocation}
                    reason={getFallbackReason({
                        appKey,
                        sdkStatus,
                        validCount: validDrains.length,
                    })}
                />
            ) : (
                <>
                    <div ref={containerRef} className="absolute inset-0" />
                    {mapDisplayStatus === "loading" && (
                        <div className="absolute inset-0 flex items-center justify-center bg-slate-50 text-sm font-medium text-slate-500">
                            Kakao 지도를 불러오고 있습니다.
                        </div>
                    )}
                </>
            )}

            <MapLegend legendCounts={legendCounts} />
        </div>
    );

    function clearKakaoMarkers() {
        markerRefs.current.forEach((marker) => marker.setMap(null));
        markerRefs.current = [];
        overlayRef.current?.setMap(null);
        overlayRef.current = null;
    }
}

function FallbackRiskMap({
    drains,
    selectedId,
    onSelect,
    labelLocation,
    reason,
}: {
    drains: DrainFacility[];
    selectedId?: string | null;
    onSelect?: (id: string) => void;
    labelLocation?: string;
    reason: string;
}) {
    return (
        <>
            <MockStreetBackground />
            <div className="absolute right-4 top-4 z-20 flex flex-col overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
                <button
                    className="flex size-9 items-center justify-center text-slate-600 hover:bg-slate-50"
                    aria-label="확대"
                    type="button"
                >
                    <Plus className="size-4" />
                </button>
                <div className="h-px w-full bg-slate-200" />
                <button
                    className="flex size-9 items-center justify-center text-slate-600 hover:bg-slate-50"
                    aria-label="축소"
                    type="button"
                >
                    <Minus className="size-4" />
                </button>
            </div>
            <div className="absolute right-4 top-[120px] z-20 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
                <button
                    className="flex size-9 items-center justify-center text-slate-600 hover:bg-slate-50"
                    aria-label="현재 위치"
                    type="button"
                >
                    <Crosshair className="size-4" />
                </button>
            </div>
            <div className="absolute bottom-4 left-4 right-4 z-20 flex items-start gap-2 rounded-lg border border-amber-200 bg-white/95 px-3 py-2 text-xs text-amber-700 shadow-sm backdrop-blur">
                <AlertTriangle className="mt-0.5 size-3.5 shrink-0" />
                <span>{reason}</span>
            </div>
            {drains.map((drain) => {
                const selected = drain.id === selectedId;
                const meta = STATUS_META[drain.status];
                return (
                    <button
                        key={drain.id}
                        onClick={() => onSelect?.(drain.id)}
                        className="absolute z-10 -translate-x-1/2 -translate-y-1/2 focus:outline-none"
                        style={{ left: `${drain.x}%`, top: `${drain.y}%` }}
                        aria-label={`${drain.id} ${drain.road}`}
                        type="button"
                    >
                        {selected && (
                            <>
                                <span className="absolute left-1/2 top-1/2 size-10 -translate-x-1/2 -translate-y-1/2 animate-ping rounded-full bg-red-400/40" />
                                <span className="absolute left-1/2 top-1/2 size-9 -translate-x-1/2 -translate-y-1/2 rounded-full bg-red-500/15 ring-2 ring-red-400" />
                            </>
                        )}
                        <span
                            className={cn(
                                "relative block size-4 rounded-full border-2 border-white shadow-md transition-transform",
                                meta.dot,
                                selected
                                    ? "scale-125 ring-2 ring-red-500"
                                    : "hover:scale-110",
                            )}
                        />
                        {selected && labelLocation && (
                            <span className="absolute left-1/2 top-7 -translate-x-1/2 whitespace-nowrap rounded-md bg-slate-900 px-2 py-1 text-[11px] font-semibold text-white shadow-md">
                                {labelLocation}
                            </span>
                        )}
                    </button>
                );
            })}
        </>
    );
}

function MapLegend({
    legendCounts,
}: {
    legendCounts: Record<RiskLevel, number>;
}) {
    return (
        <div className="absolute left-4 top-4 z-20 rounded-lg border border-slate-200 bg-white/95 px-3 py-2.5 shadow-sm backdrop-blur">
            <ul className="flex flex-col gap-1.5 text-xs font-medium text-slate-600">
                <LegendRow
                    color={STATUS_META.danger.dot}
                    label="위험"
                    count={legendCounts.danger}
                />
                <LegendRow
                    color={STATUS_META.caution.dot}
                    label="주의"
                    count={legendCounts.caution}
                />
                <LegendRow
                    color={STATUS_META.good.dot}
                    label="양호"
                    count={legendCounts.good}
                />
                <LegendRow
                    color={STATUS_META.unknown.dot}
                    label="판단불가"
                    count={legendCounts.unknown}
                />
            </ul>
        </div>
    );
}

function LegendRow({
    color,
    label,
    count,
}: {
    color: string;
    label: string;
    count: number;
}) {
    return (
        <li className="flex items-center gap-2">
            <span className={cn("size-2.5 rounded-full", color)} />
            <span>
                {label} ({count})
            </span>
        </li>
    );
}

function MockStreetBackground() {
    return (
        <svg
            className="absolute inset-0 h-full w-full"
            preserveAspectRatio="none"
            aria-hidden="true"
        >
            <rect width="100%" height="100%" fill="#f1f5f9" />
            <defs>
                <pattern
                    id="blocks"
                    width="120"
                    height="120"
                    patternUnits="userSpaceOnUse"
                >
                    <rect width="120" height="120" fill="#f8fafc" />
                    <rect
                        x="8"
                        y="8"
                        width="104"
                        height="104"
                        rx="4"
                        fill="#eef2f6"
                    />
                </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#blocks)" />
            {[15, 35, 55, 75].map((y) => (
                <line
                    key={`h${y}`}
                    x1="0"
                    y1={`${y}%`}
                    x2="100%"
                    y2={`${y}%`}
                    stroke="#e2e8f0"
                    strokeWidth="10"
                />
            ))}
            {[20, 45, 70].map((x) => (
                <line
                    key={`v${x}`}
                    x1={`${x}%`}
                    y1="0"
                    x2={`${x}%`}
                    y2="100%"
                    stroke="#e2e8f0"
                    strokeWidth="10"
                />
            ))}
            <line
                x1="0"
                y1="100%"
                x2="100%"
                y2="20%"
                stroke="#dbe3ec"
                strokeWidth="14"
            />
            <path
                d="M 100 540 C 200 480, 260 520, 340 470 S 500 430, 620 460"
                fill="none"
                stroke="#cfe3f2"
                strokeWidth="16"
                strokeLinecap="round"
                opacity="0.8"
            />
        </svg>
    );
}

function loadKakaoMapsSdk(appKey: string) {
    if (window.kakao?.maps) {
        return new Promise<void>((resolve) => {
            window.kakao?.maps.load(resolve);
        });
    }

    if (kakaoSdkPromise) return kakaoSdkPromise;

    kakaoSdkPromise = new Promise((resolve, reject) => {
        const existingScript = document.getElementById(KAKAO_SDK_ID);
        if (existingScript) {
            existingScript.addEventListener("load", () => {
                window.kakao?.maps.load(resolve);
            });
            existingScript.addEventListener("error", reject);
            return;
        }

        const script = document.createElement("script");
        script.id = KAKAO_SDK_ID;
        script.async = true;
        script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${appKey}&autoload=false`;
        script.onload = () => {
            if (!window.kakao?.maps) {
                reject(new Error("Kakao Maps SDK is unavailable."));
                return;
            }
            window.kakao.maps.load(resolve);
        };
        script.onerror = reject;
        document.head.appendChild(script);
    });

    return kakaoSdkPromise;
}

function hasValidCoordinate(drain: DrainFacility) {
    return (
        Number.isFinite(drain.latitude) &&
        Number.isFinite(drain.longitude) &&
        Math.abs(drain.latitude) <= 90 &&
        Math.abs(drain.longitude) <= 180
    );
}

function getMapCenter(drains: DrainFacility[]) {
    if (drains.length === 0) return DEFAULT_CENTER;

    const total = drains.reduce(
        (acc, drain) => ({
            latitude: acc.latitude + drain.latitude,
            longitude: acc.longitude + drain.longitude,
        }),
        { latitude: 0, longitude: 0 },
    );

    return {
        latitude: total.latitude / drains.length,
        longitude: total.longitude / drains.length,
    };
}

function createMarkerImage(status: RiskLevel, selected: boolean) {
    const color = MARKER_COLORS[status];
    const ring = selected ? "#0f172a" : "#ffffff";
    const svg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="34" height="44" viewBox="0 0 34 44">
            <path d="M17 42C13 35 5 28 5 17C5 10.4 10.4 5 17 5C23.6 5 29 10.4 29 17C29 28 21 35 17 42Z" fill="${color}" stroke="${ring}" stroke-width="3"/>
            <circle cx="17" cy="17" r="6" fill="#ffffff" fill-opacity="0.92"/>
        </svg>
    `;
    return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function createSelectedOverlayContent(label: string) {
    const safeLabel = escapeHtml(label);
    return `
        <div style="padding:4px 8px;border-radius:6px;background:#0f172a;color:#fff;font-size:11px;font-weight:700;box-shadow:0 4px 10px rgba(15,23,42,.18);white-space:nowrap;">
            ${safeLabel}
        </div>
    `;
}

function escapeHtml(value: string) {
    return value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function getFallbackReason({
    appKey,
    sdkStatus,
    validCount,
}: {
    appKey?: string;
    sdkStatus: KakaoSdkStatus;
    validCount: number;
}) {
    if (!appKey) {
        return "Kakao Maps JavaScript 키가 없어 임시 지도를 표시합니다.";
    }
    if (validCount === 0) {
        return "사용 가능한 위도/경도 좌표가 없어 임시 지도를 표시합니다.";
    }
    if (sdkStatus === "error") {
        return "Kakao Maps SDK를 불러오지 못해 임시 지도를 표시합니다.";
    }
    return "Kakao 지도를 준비하는 동안 임시 지도를 표시합니다.";
}
