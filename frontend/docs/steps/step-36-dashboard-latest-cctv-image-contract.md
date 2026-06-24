# 36 대시보드 최신 CCTV 이미지 계약 연동

## 작업 결과

메인 대시보드의 선택 시설 패널이 목록 응답의 최신 CCTV 이미지 URL을 사용하도록 준비했다. 이미지가 없으면 기존 placeholder를 그대로 사용하므로, 백엔드 배포 전에도 화면이 깨지지 않는다.

또한 `YOLO_RESULT_UPDATED` WebSocket 이벤트를 받으면 대시보드 목록 cache의 해당 시설 최신 이미지가 즉시 갱신된다. 선택 패널은 이 cache를 사용하므로 새 분석 이미지가 도착하면 새로고침 없이 반영된다.

## 변경 전/후

| 구분 | 변경 전 | 변경 후 |
| --- | --- | --- |
| 초기 대시보드 이미지 | `GET /api/drains`에 이미지 필드가 없어 `DrainSummaryPanel`의 facility placeholder 표시 | 목록 item의 `latestImageUrl`을 선택 패널에 전달 |
| 실시간 YOLO 결과 | Zustand에 이벤트만 저장, 대시보드 목록 cache는 이미지 URL 미갱신 | `YOLO_RESULT_UPDATED.imageUrl`로 해당 시설의 cache 갱신 |
| 이미지 미제공 | placeholder | 동일하게 placeholder 유지 |

## 프론트 계약

`GET /api/drains`의 `DrainListItemDto`에 아래 optional 필드를 사용한다.

```ts
latestImageUrl?: string | null;
latestImageCapturedAt?: string | null;
```

- `latestImageUrl`: 해당 시설의 가장 최근 YOLO 분석 이미지 URL
- `latestImageCapturedAt`: 그 이미지의 촬영 시각(ISO 8601, 없으면 `null`)
- 분석 이미지가 없는 시설은 두 필드를 `null`로 반환한다.

기존 `YOLO_RESULT_UPDATED` 이벤트의 `imageUrl`, `capturedAt`, `updatedAt`은 최신 이미지를 실시간 반영하는 데 사용한다.

## 백엔드 전달용 요청문

아래 내용을 그대로 백엔드 담당 에이전트에 전달할 수 있다.

```text
대시보드 선택 시설 패널에 상세 화면과 같은 최신 CCTV 이미지를 표시하려고 합니다.

GET /api/drains의 각 DrainListItemDto에 아래 optional 필드를 추가해주세요.
- latestImageUrl: string | null  // 가장 최근 YOLO 분석 이미지 URL
- latestImageCapturedAt: string | null  // 해당 이미지 capturedAt, ISO 8601

규칙:
1. 최신 기준은 가장 최근 YOLO 분석 결과의 capturedAt(동률이면 analyzedAt 또는 생성시각)입니다.
2. 분석 이미지가 없으면 두 필드는 null입니다.
3. 기존 필드와 endpoint는 변경하지 않는 하위 호환 추가입니다.
4. 새 YOLO 분석 결과 저장 후 WS /ws/drains/status로 아래 이벤트를 발행해주세요.
   type: YOLO_RESULT_UPDATED
   payload: drainId, yoloResultId, imageUrl, obstructionRatio, confidenceScore,
            yoloStatus, capturedAt, analyzedAt, updatedAt

프론트는 목록의 latestImageUrl로 초기 이미지를 표시하고,
YOLO_RESULT_UPDATED.imageUrl로 실시간 갱신합니다.
```

## 백엔드 적용 전 확인 방법

`GET /api/drains` 응답의 한 item에 다음과 같이 이미지 값이 포함되는지 확인한다.

```json
{
  "id": "DR-004",
  "latestImageUrl": "https://.../drain-004/latest.jpg",
  "latestImageCapturedAt": "2026-06-24T10:30:00+09:00"
}
```

`YOLO_RESULT_UPDATED` 수신 뒤 대시보드에서 해당 시설을 선택한 상태로 이미지가 즉시 바뀌는지도 확인한다.

## 검증 결과

검증 명령 결과는 아래 표에 기록한다.

| 명령어 | 결과 | 비고 |
| --- | --- | --- |
| `npm.cmd run lint` | 통과 | 오류 0건. 기존 `FallbackImage`의 `<img>` 성능 경고 1건 유지 |
| `npm.cmd run build` | 통과 | Next.js production build 성공. `/` 정적 생성 및 `/drains/[id]` 동적 route 확인 |

## 남은 작업

- 백엔드가 `latestImageUrl`, `latestImageCapturedAt`을 제공하면 실제 API·WebSocket 환경에서 초기 표시와 실시간 갱신을 확인한다.
- 메타데이터 이미지 추가, 상세 차트 이중 Y축, 미사용 이미지 정리는 plan-23 범위에서 계속 진행한다.
