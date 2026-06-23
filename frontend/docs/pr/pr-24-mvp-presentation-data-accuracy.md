## 작업 내용

- MVP API 계약에 맞춰 수위는 cm, 유속은 m/s, 막힘률은 %로 표시한다.
- 실제 기간 조회가 아닌 차트 탭·기준선·최고값 문구를 제거한다.
- 위험 점수 대신 최종 위험 상태와 판단 문구를 중심으로 상세 UI를 구성한다.
- 최신 센서값 선택, nullable DTO, API 오류 표시를 보완한다.

## 검증 결과

- `npm.cmd exec tsc -- --noEmit` 통과
- `npm.cmd run build` 통과
- `npm.cmd run lint` 오류 없음 (기존 `<img>` 경고 1건)

## 비고

- 백엔드 API와 WebSocket 계약 및 새 패키지는 변경하지 않았다.
