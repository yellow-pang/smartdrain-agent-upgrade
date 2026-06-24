# 42 Frontend 번들 측정 기준선 확보 결과

## 작업 목표

보안·성능 리팩터링 전에 실제 client bundle 구성을 확인했다. 측정 결과만으로 지도·차트의 lazy loading이나 Client Component 구조를 변경하지 않고, 다음 판단에 필요한 기준선을 남기는 데 집중했다.

## 변경 내용

| 파일 | 변경 내용 |
| --- | --- |
| `package.json` | `@next/bundle-analyzer`를 devDependency로 추가 |
| `pnpm-lock.yaml` | 분석 도구 의존성 lockfile 반영 |
| `next.config.mjs` | `ANALYZE=true`에서만 bundle analyzer wrapper가 활성화되도록 추가 |
| `docs/plans/plan-28-frontend-security-performance-hardening.md` | 측정 결과와 다음 승인 항목 기록 |

분석 도구는 개발·측정 전용이며, 기본 production build와 브라우저 런타임에 포함되지 않는다.

## 측정 명령과 결과

| 명령 | 결과 | 비고 |
| --- | --- | --- |
| `ANALYZE=true pnpm build` | build 통과, 리포트 미생성 | Next.js 16 기본 Turbopack build는 `@next/bundle-analyzer`와 호환되지 않음 |
| `ANALYZE=true pnpm exec next build --webpack` | 통과, `client.html` 등 분석 리포트 생성 | 측정 전용 Webpack build. 기본 build 설정은 유지 |

클라이언트 리포트 기준 주요 수치는 다음과 같다.

| chunk | parsed | gzip | 포함 내용 |
| --- | ---: | ---: | --- |
| 공통 client chunk | 약 354KB | 약 103KB | `recharts`, `react-kakao-maps-sdk`와 하위 의존성 |
| 대시보드 route 전용 | 약 29KB | 약 7KB | 대시보드 표시 컴포넌트 |
| 상세 route 전용 | 약 31KB | 약 8KB | 상세 표시 컴포넌트 |

## 결정

- 대시보드 지도는 핵심 첫 화면 기능이므로 지연 로딩하지 않는다.
- 공통 chunk가 큰 사실만으로 차트를 dynamic import하지 않는다. 실제 모바일 LCP·입력 반응·네트워크 조건을 추가 측정한 뒤 적용 여부를 다시 결정한다.
- Zod, React Hook Form, virtualization, CSP, `next/image` 전환은 이번 단계에 도입하지 않았다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| Webpack analyzer build | 통과 |
| TypeScript | Webpack production build 단계에서 통과 |
| 기본 Turbopack build | 앞선 기준선에서 통과. analyzer 리포트만 생성되지 않음 |

## 다음 단계

실제 모바일 환경에서 대시보드 첫 표시와 상세 차트 진입의 성능을 측정한다. 차트 지연 로딩이 사용자 체감 지연을 줄일 근거가 생길 때만 별도 승인을 받아 적용한다.
