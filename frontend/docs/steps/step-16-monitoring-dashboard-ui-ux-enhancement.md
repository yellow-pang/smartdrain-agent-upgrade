# 16 모니터링 대시보드 UI/UX 고도화 결과

## 작업 결과

- 대시보드를 화면 높이를 채우는 셸로 정리하고, `xl` 이상 지도·위험 목록, `2xl` 이상 지도·위험 목록·상세 패널에 공통 관제 높이를 적용했다.
- 위험 목록은 외곽 패널 안에서만 스크롤하고, 기본 항목의 이중 테두리·그림자를 줄였다. 긴 시설명과 판단 문구는 줄 수를 제한하고 전체 값을 `title`로 확인할 수 있다.
- 상세 화면의 공용 지도에 `dashboard`/`detail` 높이 variant를 도입했다. 상세 지도는 카드가 정한 `220~260px` 높이를 따르므로 기존 `420px` 최소 높이 충돌이 제거된다.
- 센서 차트·요약 카드·tooltip을 다크 테마 표면에 맞췄고, grid/축 색상은 CSS 토큰으로 라이트·다크에서 분리했다.
- 메뉴와 사용자 버튼은 기능 예정 안내를 버튼 주변에 2.5초간 표시한다. 바깥 클릭, Escape, 다른 버튼 클릭으로도 닫힌다.
- 좁은 대시보드 상세 패널에서는 상태를 인라인 배지로 압축하고, 판정 결과는 전체 폭의 문장 영역으로 표시한다. 주소 행은 라벨을 고정하고 값이 여러 줄이어도 글자 단위로 세로 분리되지 않게 했다.
- 센서 요약 카드는 중간 폭에서 2열을 유지하고, 상태 배지와 수치에 줄바꿈 방지 규칙을 적용해 `주의`·단위가 글자 단위로 분리되지 않게 했다.

## 변경 파일

| 파일 | 변경 내용 |
| --- | --- |
| `app/page.tsx` | 대시보드 배경 셸, 3패널 공통 높이, 지도 flex 영역 정리 |
| `app/globals.css` | 전역 최소 높이와 차트 grid/axis 테마 토큰 추가 |
| `app/drains/[id]/page.tsx` | 상세 위치 지도에 `detail` variant 지정 |
| `components/risk-map.tsx` | 대시보드·상세 화면별 지도 최소 높이 정책 분리 |
| `components/sensor-trend-chart.tsx` | 다크 차트 카드, tooltip, 요약 카드와 SVG 축/grid 테마 반영 |
| `components/drain-risk-list.tsx` | 목록 항목의 테두리 밀도와 긴 텍스트 처리 개선 |
| `components/app-header.tsx` | 메뉴·사용자 버튼의 기능 예정 피드백 연결 |
| `components/coming-soon-popover.tsx` | 자동 닫힘·바깥 클릭·Escape를 지원하는 안내 팝오버 추가 |

## 검증 결과

| 검증 | 결과 | 비고 |
| --- | --- | --- |
| `pnpm lint` | 통과 | 신규 error 없음. 기존 `fallback-image.tsx`의 native `<img>` warning 1건 유지 |
| `pnpm exec tsc --noEmit` | 통과 | 타입 오류 없음 |
| `git diff --check` | 통과 | 공백 오류 없음 |
| `pnpm build` | 보류 | 코드 오류가 아닌 Google Fonts(`Geist`, `Geist Mono`) 네트워크 다운로드 실패로 중단 |
| 브라우저 수동 확인 | 필요 | 실제 Kakao 지도 resize/relayout, 화면 크기별 패널 높이, 라이트·다크 테마, 팝오버 상호작용 확인 필요 |

## 남은 리스크

- Kakao Maps SDK가 브라우저 resize 뒤 컨테이너 크기를 즉시 반영하는지 실제 API 키 환경에서 확인이 필요하다.
- production build는 네트워크가 가능한 환경에서 Google Fonts를 가져올 수 있는지 재실행해야 한다.
- 긴 실제 시설명·판단 문구와 다수 시설 데이터로 목록 스크롤의 체감 밀도를 추가 확인해야 한다.

## 제안 커밋 메시지

```text
refactor: 모니터링 대시보드 UI와 UX 고도화

- 지도·위험 목록·상세 패널의 관제 높이와 내부 스크롤을 정리한다.
- 상세 지도 overflow를 화면별 지도 높이 variant로 해결한다.
- 센서 차트의 다크 테마와 메뉴·사용자 기능 예정 안내를 추가한다.
```
