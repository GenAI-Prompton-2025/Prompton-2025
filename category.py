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

def classify_post(keywords, categories):
    functions = [
        {
            "name": "classify_post",
            "description": "게시글의 키워드를 기반으로 적절한 카테고리 분류",
            "parameters": {
                "type": "object",
                "properties": {
                    "primary_category": {
                        "type": "string",
                        "description": "주요 카테고리"
                    },
                    "secondary_category": {
                        "type": "string",
                        "description": "부가 카테고리"
                    }
                },
                "required": ["primary_category", "secondary_category"]
            }
        }
    ]

    categories_info = json.dumps(categories, ensure_ascii=False)
    prompt = f"""
    다음 키워드를 가진 게시글을 주어진 카테고리 중에서 분류해주세요.
    
    키워드: {keywords}
    
    가능한 카테고리:
    {categories_info}
    
    가장 적합한 주요 카테고리 1개와 부가 카테고리 1개를 선택해주세요.
    """

    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "당신은 데이터 분류 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            functions=functions,
            function_call={"name": "classify_post"},
            temperature=0.3
        )
        return json.loads(response.choices[0].message.function_call.arguments)
    except Exception as e:
        print(f"게시글 분류 중 오류 발생: {e}")
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
    
    # 결과 DataFrame 준비
    df['primary_category'] = ''
    df['secondary_category'] = ''
    
    # 각 게시글 분류
    for idx, row in df.iterrows():
        print(f"Processing row {idx + 1}/{len(df)}")
        keywords = row['keywords'].split(';') if isinstance(row['keywords'], str) else []
        result = classify_post(keywords, categories_result['categories'])
        
        if result:
            df.at[idx, 'primary_category'] = result['primary_category']
            df.at[idx, 'secondary_category'] = result['secondary_category']
        
        if (idx + 1) % 10 == 0:
            time.sleep(1)  # API 호출 제한 방지
    
    # 결과 저장
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    # 카테고리 정보 별도 저장
    categories_df = pd.DataFrame(categories_result['categories'])
    categories_df.to_csv('refine_result/categories.csv', index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    input_file = 'refine_result/output3.csv'
    output_file = 'refine_result/categorized_output.csv'
    process_csv(input_file, output_file)
