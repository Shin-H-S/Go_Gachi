# backend/check_models.py
from app.core.config import settings

def check_models():
    if not settings.openai_enabled:
        print("OPENAI_API_KEY가 설정되지 않았습니다. backend/.env를 확인하세요.")
        return

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        models = client.models.list()
        model_ids = sorted([m.id for m in models.data])
        
        print(f"--- [할당된 전체 모델 리스트] (총 {len(model_ids)}개) ---")
        
        # 필터링 없이 리스트에 있는 모든 모델을 순서대로 출력합니다.
        for m_id in model_ids:
            print(m_id)
            
        print("--------------------------------------------------")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    check_models()
