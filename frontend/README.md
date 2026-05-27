This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

<<<<<<< Updated upstream
## Getting Started
=======
카페 메뉴 광고 이미지 제작용 Streamlit 프론트엔드입니다.
이미지 업로드, 광고 채널 선택, 프롬프트 입력, 생성 중 로딩 UI, 결과 미리보기를 제공합니다.
>>>>>>> Stashed changes

First, run the development server:

<<<<<<< Updated upstream
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.
=======
```text
frontend/
  app.py                # Streamlit 프론트엔드 진입점
  app/                  # 향후 컴포넌트 분리용 폴더
    components/         # 재사용 UI 컴포넌트 작성 위치
  assets/               # 샘플 이미지, 아이콘 등 정적 리소스
  tests/                # 프론트엔드 테스트 코드
  .env.example          # 배포된 백엔드 URL 예시
  requirements.txt      # Streamlit 개발 시작용 의존성
```

## Run

레포 루트에서 프론트 의존성을 설치한 뒤 실행합니다.

```bash
pip install -r requirements-frontend.txt
streamlit run frontend/app.py
```

## Backend Connection
>>>>>>> Stashed changes

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

<<<<<<< Updated upstream
To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
=======
- `GET /api/config`: 광고 프리셋 목록 조회
- `POST /api/generate`: `imageDataUrl`, `presetId`, `feedback`을 전달해 생성 요청

`BACKEND_URL`이 없으면 프론트 화면 확인을 위해 mock 결과 이미지를 표시합니다.
>>>>>>> Stashed changes
