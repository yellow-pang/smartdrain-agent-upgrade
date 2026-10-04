# SmartDrain AI Service Guidelines

이 파일은 `ai_service/` 내부 작업에 적용됩니다.

루트 `AGENTS.md`의 공통 규칙을 함께 적용합니다.

## 1. AI Service 책임

AI Service는 다음 책임을 가집니다.

- 입력 이미지 검증
- OpenCV 기반 전처리
- YOLO 추론
- 막힘 비율과 신뢰도 계산
- XGBoost 위험도 예측
- 분석 결과 생성
- Backend callback 전송
- AI 분석 오류 매핑

AI Service는 DB에 직접 접근하지 않습니다.

분석 결과 저장은 Backend가 담당합니다.

## 2. 계층 분리

모델 계층과 HTTP 통신 계층을 분리합니다.

YOLO, OpenCV, XGBoost 모델 계층은 다음 내용을 알지 않도록 유지합니다.

- Backend URL
- HTTP callback 정책
- timeout
- retry
- HTTP status code
- 인증 header

다음 책임은 HTTP 또는 integration 계층에서 처리합니다.

- Backend callback
- timeout
- retry
- HTTP 오류 처리
- request와 response 변환
- 네트워크 로그

## 3. 모델 처리

- 모델 입력과 출력 타입을 명확히 합니다.
- 이미지 전처리 기준을 여러 위치에 중복 작성하지 않습니다.
- confidence와 obstruction ratio의 단위 및 범위를 명시합니다.
- 모델 파일이 없을 때의 동작을 구분합니다.
- mock 분석과 실제 분석 경로를 혼동하지 않습니다.
- 모델 결과가 없거나 신뢰할 수 없는 경우를 명시적으로 처리합니다.
- 판단 불가 상태를 단순 오류와 구분합니다.

## 4. Callback

Backend callback 계약을 변경할 때는 Backend consumer를 함께 확인합니다.

다음 항목을 고려합니다.

- 분석 요청 식별자
- drain 식별자
- 분석 상태
- 결과 payload
- 오류 payload
- timeout
- 재시도
- 중복 callback
- 순서가 뒤바뀐 결과
- Backend 응답 실패

callback 실패가 모델 추론 결과 자체를 손상시키지 않도록 책임을 분리합니다.

## 5. 의존성과 모델 파일

AI Service 런타임 의존성은 `ai_service/requirements.txt`를 기준으로 관리합니다.

다음 파일은 Git에 커밋하지 않습니다.

- 실제 모델 가중치
- 대용량 학습 데이터
- 로컬 캐시
- 비밀값
- 임시 추론 결과
- 생성된 로그

모델 파일을 새로 생성하거나 이동하기 전에 다음을 확인합니다.

- 저장 위치
- `.gitignore`
- Docker volume 또는 COPY 경로
- 운영 환경 배포 방식
- 파일이 없는 환경에서의 테스트 가능성

## 6. 테스트

실제 모델 파일이나 외부 네트워크가 없어도 실행 가능한 테스트를 우선합니다.

우선 테스트할 대상은 다음과 같습니다.

- 입력 validation
- 이미지 전처리
- 결과 변환
- 위험 상태 mapping
- callback payload 생성
- HTTP 오류 mapping
- retry 정책
- 모델 adapter

모델 호출은 가능한 경우 adapter 또는 mock 경계를 통해 대체합니다.

## 7. 검증

검증 기준은 `docs/reference/verification-guide.md`를 우선 확인합니다.

작업 전 다음을 확인합니다.

- `ai_service/requirements.txt`
- 실행 진입점
- pytest 설정
- 모델 경로 설정
- callback 설정
- Docker 실행 명령
- CI 검증 명령

현재 AI Service 의존성은 `ai_service/requirements.txt`로 관리하며 실행 진입점은 `ai_service.http.app:app`입니다.

저장소에 구성된 범위에서 다음을 실행합니다.

```bash
cd ai_service
python -m pytest
```

필요한 경우 Python import와 compile 검사를 수행합니다.

```bash
python -m compileall .
```

실제 모델 파일이 없어 실행하지 못한 검증은 최종 보고에 명확히 작성합니다.
