# Font Assets

이 폴더는 이미지 텍스트 합성에 사용할 폰트 파일과 라이선스 파일을 보관합니다.
서버 환경마다 설치된 시스템 폰트가 다를 수 있으므로, 광고 이미지 결과를 일정하게 만들기 위해
배포 이미지에 포함되는 정적 자산으로 관리합니다.

## 현재 포함된 폰트

| 폰트 | 파일 | 주요 용도 | 출처 | 라이선스 |
| --- | --- | --- | --- | --- |
| Pretendard | `Pretendard-Regular.otf`, `Pretendard-Bold.otf` | 기본 한글/영문/숫자 광고 문구 | https://github.com/orioncactus/pretendard | `OFL.txt` |
| SUIT | `SUIT-Regular.ttf`, `SUIT-Bold.ttf` | 단정한 정보성 문구 후보 | https://github.com/sun-typeface/SUIT | `SUIT-OFL.txt` |
| Noto Sans KR | `NotoSansKR-Variable.ttf` | 한글 fallback 후보 | https://github.com/google/fonts/tree/main/ofl/notosanskr | `NotoSansKR-OFL.txt` |
| Inter | `Inter-Variable.ttf` | 영문/숫자 포인트 후보 | https://github.com/google/fonts/tree/main/ofl/inter | `Inter-OFL.txt` |
| Montserrat | `Montserrat-Variable.ttf` | 이벤트/프로모션 영문 포인트 후보 | https://github.com/google/fonts/tree/main/ofl/montserrat | `Montserrat-OFL.txt` |
| Poppins | `Poppins-Regular.ttf`, `Poppins-Bold.ttf` | 이벤트/프로모션 영문 포인트 후보 | https://github.com/google/fonts/tree/main/ofl/poppins | `Poppins-OFL.txt` |

## 사용 정책

- 기본 렌더링 폰트는 `Pretendard-Regular.otf`, `Pretendard-Bold.otf`입니다.
- 한글 문구는 Pretendard, SUIT, Noto Sans KR 중 하나를 우선 사용합니다.
- Inter, Montserrat, Poppins는 한글 지원용이 아니므로 영어/숫자 강조 문구에만 사용합니다.
- 폰트 파일은 원본 그대로 보관하고 임의 수정하지 않습니다.
- 폰트 파일을 수정하거나 subset으로 재가공해야 한다면, 새 파일명과 라이선스 조건을 다시 검토합니다.
- 새 폰트를 추가할 때는 폰트 파일과 라이선스 파일을 함께 추가하고, 이 문서의 표를 갱신합니다.
- 폰트 단독 판매는 하지 않습니다. 앱/이미지 생성 결과물에 포함해 사용하는 용도로만 관리합니다.

## 배포 전 확인

- `.dockerignore`가 `backend/app/assets/fonts/`를 제외하지 않는지 확인합니다.
- 배포 환경(Railway·VM 등)에서 `backend/app/assets/fonts/`가 함께 포함되는지 확인합니다.
- 폰트 선택 로직을 바꿀 때는 Pillow 로딩 테스트와 텍스트 합성 테스트를 함께 실행합니다.

```powershell
uv run python -c "from pathlib import Path; from PIL import ImageFont; base=Path('backend/app/assets/fonts'); print(ImageFont.truetype(str(base/'Pretendard-Regular.otf'), 32).getname())"
uv run pytest -p no:cacheprovider tests\test_text_composition.py
```
