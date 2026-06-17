import type { DrainDetailDto, DrainListItemDto } from "@/lib/api/types";
import type { DrainFacility, RiskHistoryItem } from "@/lib/mock-data";

function clampPercent(value: number) {
    return Math.min(100, Math.max(0, Math.round(value)));
}

function ratioToPercent(value: number) {
    return clampPercent(value <= 1 ? value * 100 : value);
}

function cmToMeter(value: number) {
    return +(value / 100).toFixed(2);
}

function waterLevelToPercent(value: number) {
    return clampPercent(value);
}

export function drainListItemDtoToFacility(
    dto: DrainListItemDto,
): DrainFacility {
    const obstructionPercent = ratioToPercent(dto.obstructionRatio);
    return {
        id: dto.id,
        road: dto.roadAddress,
        fullAddress: dto.fullAddress ?? dto.roadAddress,
        status: dto.riskLevel,
        blockage: obstructionPercent,
        waterLevelPct: waterLevelToPercent(dto.waterLevelCm),
        waterLevelM: cmToMeter(dto.waterLevelCm),
        flow: dto.flowVelocityMps,
        updatedAt: dto.updatedAt,
        judgement: dto.finalDecision,
        x: 50,
        y: 50,
    };
}

export function drainDetailDtoToFacility(dto: DrainDetailDto): DrainFacility {
    return drainListItemDtoToFacility(dto);
}

export function riskHistoryDtoToItem(
    item: NonNullable<DrainDetailDto["riskHistory"]>[number],
): RiskHistoryItem {
    return {
        time: item.changedAt,
        status: item.riskLevel,
        score: item.riskScore,
    };
}
