# 37 상세 센서 이중 Y축 차트 및 이미지 사용처 점검 결과

## 작업 결과

상세 화면의 센서 차트를 수위와 유속의 이중 Y축으로 분리했다. 수위는 왼쪽 축(cm), 유속은 오른쪽 축(m/s)을 사용하므로 값 범위 차이로 유속 선이 하단에 붙어 보이던 문제가 해소된다.

`frontend/public/images`의 모든 이미지 파일은 현재 코드에서 참조되고 있어 삭제하지 않았다.

## 차트 표시 기준

| 데이터 상태 | 표시 방식 |
| --- | --- |
| API 연결 대기 | 기존 `API 데이터 대기` placeholder |
| 측정 이력 0건 | `측정 이력 없음` placeholder |
| 측정 이력 1건 | 수위·유속 점만 표시하고 추세 데이터 부족 안내 |
| 측정 이력 2건 이상 | 수위와 유속을 각 축에 연결한 추세선 |

## 이중 Y축 정책

| 데이터 | 축 | 기본 범위 | 초과 값 처리 |
| --- | --- | --- |
| 수위 | 왼쪽, cyan 계열 | 0~25 cm | 최댓값에 맞춰 상한 확장 |
| 유속 | 오른쪽, green 계열 | 0~1.5 m/s | 최댓값에 맞춰 상한 확장 |

축·선·범례의 색상을 일치시키고, 툴팁은 기존처럼 각 값의 단위를 표시한다.

## 이미지 점검 결과

| 경로 | 결과 |
| --- | --- |
| `public/images/metaimage/smartdrain-icon.png` | 앱·Apple 아이콘으로 사용 중 |
| `public/images/metaimage/smartdrain-og-image.png` | Open Graph·Twitter 이미지로 사용 중 |
| `public/images/placeholder/*.png` 5개 | CCTV, 지도, 차트, 시설, 썸네일 fallback으로 사용 중 |

삭제 후보는 없으며, `/test-snapshots/*`는 `public/images`와 별개의 통합 테스트 자산 경로로 유지한다.

## 검증 결과

| 명령어 | 결과 | 비고 |
| --- | --- | --- |
| `npm.cmd run lint` | 통과 | 오류 0건, 기존 `FallbackImage`의 `<img>` 성능 경고 1건 유지 |
| `npm.cmd run build` | 통과 | Next.js production build 성공 |
| `npx.cmd tsc --noEmit` | 통과 | 이중 Y축 Recharts props와 축 범위 계산 타입 확인 |
| `rg` 이미지 참조 검색 | 통과 | `public/images`의 7개 이미지 모두 사용 중 |

## 남은 확인 사항

- 실제 브라우저에서 0건·1건·다건 센서 이력과 수위 25 cm/유속 1.5 m/s 초과 값을 확인한다.
- 실제 API 응답 수위·유속 분포에 맞춰 기본 축 범위가 적절한지 운영 데이터 기준으로 재확인한다.
