import pandas as pd
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import json
import time

# .env 파일 로드
load_dotenv()

endpoint = os.getenv("ENDPOINT_URL")  
# deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4o-mini")
deployment = "gpt-4o-mini"
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")  

# Azure OpenAI 설정
client = AzureOpenAI(
    azure_endpoint=endpoint,  
    api_key=subscription_key,  
    api_version="2024-05-01-preview",
)

def create_categories(keywords_list):
    functions = [
        {
            "name": "create_categories",
            "description": "키워드 리스트를 분석하여 상위 카테고리 생성",
            "parameters": {
                "type": "object",
                "properties": {
                    "categories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "카테고리 이름"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "카테고리 설명"
                                },
                                "related_keywords": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "관련 키워드 목록"
                                }
                            },
                            "required": ["name", "description", "related_keywords"]
                        }
                    }
                },
                "required": ["categories"]
            }
        }
    ]

    prompt = f"""
    다음 키워드 목록을 분석하여 10개의 대표적인 카테고리를 생성해주세요:
    {keywords_list}

    각 카테고리는 다음 기준을 따라야 합니다:
    1. 포괄적이면서도 구체적인 주제를 나타내야 함
    2. 중복되지 않아야 함
    3. 명확한 구분이 가능해야 함
    4. 관련 키워드들을 포함할 수 있어야 함
    """

    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "당신은 데이터 분류 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            functions=functions,
            function_call={"name": "create_categories"},
            temperature=0.7
        )
        return json.loads(response.choices[0].message.function_call.arguments)
    except Exception as e:
        print(f"카테고리 생성 중 오류 발생: {e}")
        return None


def process_csv(input_file, output_file):
    # CSV 파일 읽기
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    
    # 모든 키워드 추출
    all_keywords = set()
    for keywords in df['keywords'].str.split(';'):
        if isinstance(keywords, list):
            all_keywords.update([k.strip() for k in keywords])
    
    # 카테고리 생성
    categories_result = create_categories(list(all_keywords))
    if not categories_result:
        return
    
        # 카테고리 결과를 JSON 파일로 저장
    with open('refine_result/categories.json', 'w', encoding='utf-8') as f:
        json.dump(categories_result, f, ensure_ascii=False, indent=2)
    
    print("카테고리가 categories.json 파일로 저장되었습니다.")
    print(categories_result)

process_csv('refine_result/output2.csv', 'refine_result/categorized_output.csv')