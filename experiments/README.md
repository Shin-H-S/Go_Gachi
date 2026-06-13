# 프롬프트 배치 테스트 (prompt lab)

시스템/문구/유저 프롬프트를 [케이스 × 이미지 × 반복] 조합으로 한 번에 생성하고,
HTML 그리드에서 결과를 한눈에 비교하며, AI가 프롬프트 준수 여부를 자동 채점한다.

서비스의 프롬프트 조립 코드(`backend/app/core/prompts.py`)를 그대로 import해서 쓰므로
여기서 검증한 프롬프트는 서비스에서도 동일하게 동작한다. `/api/generate`의 캐시를 거치지
않고 `call_openai_edit`를 직접 호출하므로 같은 조합도 매번 새로 생성된다(편차 테스트 가능).

## 준비

```bash
uv add --dev pyyaml      # 최초 1회 (yaml 매트릭스용. json만 쓰면 불필요)
# .env에 OPENAI_API_KEY 필요 (레포 공통 .env 그대로 사용)
```

## 사용 흐름

### A. 테스트 콘솔 (GUI, 권장)

```bash
uv run streamlit run experiments/app.py
```

탭1 (새 테스트): 테스트명(기본값=날짜·시간) → 설정 불러오기(이전 테스트 재사용) →
이미지 업로드 → 채널·유형·문구 프롬프트 선택(전부 직접입력 가능) → 갯수 정해 생성.
백그라운드로 돌기 때문에 기다리지 않고 바로 다음 테스트를 돌릴 수 있다.

탭2 (결과·평가): 생성 이미지가 번호와 함께 표로 나오고, 그 아래 평가표에서
항목별로 평가자(사람/AI)와 내용을 정해 0~10점으로 채점한다 (기본 6항목 + 항목 추가).
마지막 열은 항목별 평균, 하단에 총점(평균의 평균). 'AI가 평가하기'는 Responses API로
AI 지정 항목을 자동 채점하고, '저장하기'는 run 폴더의 evaluation.json에 보관한다.
설정값 정리·비용(생성+평가 추정)·메모도 같은 화면에 있다.

run 폴더 구조: config.json(설정), results.json(생성 기록), evaluation.json(평가표+메모),
images/(결과), inputs/(입력 사본) — 폴더 하나가 자기완결이라 폴더째 공유 가능.

### B. CLI (대량 매트릭스용)

```bash
# 1) 프롬프트만 확인 (API 호출 X, 비용 0)
uv run python experiments/runner.py experiments/matrix.example.yaml --dry-run

# 2) 실제 생성 (실행 전 조합 수와 예상 비용을 보여주고 확인받음)
uv run python experiments/runner.py experiments/matrix.example.yaml

# 3) AI 자동 채점 (생략 가능)
uv run python experiments/judge.py experiments/runs/<run_id>

# 4) HTML 리포트 생성 → 브라우저로 열기
uv run python experiments/report.py experiments/runs/<run_id>
```

결과는 `experiments/runs/<날짜_시각_run_name>/`에 저장된다:
`results.json`(전체 기록 + 프롬프트 전문 + 채점), `images/`(결과), `inputs/`(입력 사본),
`report.html`(그리드 리포트 — 상대경로라 폴더째 압축해 팀에 공유 가능).

## 매트릭스 작성법

`matrix.example.yaml` 참고. 케이스 필드:

| 필드 | 설명 |
|---|---|
| `id` | 케이스 고유 이름 (결과 파일명·리포트 행 제목) |
| `kind` | `system` / `copy` / `user` / `mixed` — 리포트 필터용 분류 |
| `preset`, `detail` | `config/presets.json`의 채널/상세 유형 id |
| `user_prompt` | 유저 입력 프롬프트 |
| `copy` | `{headline, subcopy, cta}` — 이미지에 렌더할 광고 문구 |
| `system_append` | 기존 시스템 프롬프트 뒤에 한 줄 추가 (A/B 비교에 적합) |
| `system_override` | 시스템 프롬프트 전체 교체 (새 프롬프트 실험) |
| `resize_mode` | `cover`(기본) / `contain` |

전역 옵션: `repeat`(반복 횟수), `concurrency`, `quality`, `model`, `run_name`.
CLI로도 덮어쓸 수 있다: `--repeat 3 --quality low --limit 5 --yes` 등.

## 채점 항목 (judge.py)

제품 보존 / 구도·레이아웃 / 문구 정확도(문구 케이스만) /
금지 요소 없음 / 종합(1~5) + verdict(pass/warn/fail) + 발견된 문제 목록.
케이스별 평균과 min~max가 터미널에 출력되고, 리포트 셀 우상단에 점수 배지가 붙는다.

## 비용 팁

- 1장 ≈ $0.01 기준으로 실행 전 예상 비용을 보여준다 (`OPENAI_IMAGE_EDIT_ESTIMATED_COST_USD`).
- 구도·준수 여부 확인은 `quality: low`로 충분한 경우가 많다. 최종 후보만 medium/high 재실행.
- `--limit N`으로 앞 N개 조합만 돌려 매트릭스를 빠르게 검증할 수 있다.

## 프롬프트 채택 후

좋은 프롬프트를 찾아 `prompts.py`/`presets.json`에 반영할 때는 `PROMPT_VERSION`을 올려
캐시를 무효화해야 한다 (`backend/app/core/prompts.py` 상단 주석 참고).
