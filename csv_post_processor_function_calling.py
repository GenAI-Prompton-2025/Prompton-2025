import pandas as pd
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import time
import json

# .env 파일 로드
load_dotenv()

endpoint = os.getenv("ENDPOINT_URL")  
deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4o")  
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")  

# Azure OpenAI 설정
client = AzureOpenAI(
    azure_endpoint=endpoint,  
    api_key=subscription_key,  
    api_version="2024-05-01-preview",
)

# 폴더 생성
os.makedirs("crawling_result", exist_ok=True)
os.makedirs("refine_result", exist_ok=True)


def process_text_with_gpt(prompt, index):
    functions = [
        {
            "name": "process_posts",
            "description": "여러 게시글과 댓글을 분석하여 정제된 형식으로 출력",
            "parameters": {
                "type": "object",
                "properties": {
                    "posts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "description": "정제된 게시글 내용"
                                },
                                "comments": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "정제된 댓글 목록"
                                },
                                "keywords": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "추출된 키워드 목록 (3-5개)"
                                },
                                "tendency": {
                                    "type": "string",
                                    "enum": ["경험성", "질문성"],
                                    "description": "게시글의 성향"
                                }
                            },
                            "required": ["content", "comments", "keywords", "tendency"]
                        }
                    }
                },
                "required": ["posts"]
            }
        }
    ]

    system_prompt = """
    당신은 게시글 분석 및 정제 전문가입니다. 게시글의 타이틀, 내용, 댓글을 분석하여 핵심 정보를 추출하고 일관된 형식으로 재작성해야 합니다.

    # 주요 목표
    1. 게시글과 댓글의 핵심 내용을 파악하고 정제된 형식으로 재작성
    2. 주요 키워드 추출
    3. 게시글의 성향 분석 (경험성/질문성)
    4. 일관된 형식으로 출력물 생성

    # 처리 단계
    1. 게시글 분석
       - 타이틀과 내용의 주제 파악
       - 핵심 메시지 추출
       - 맥락 이해 및 성향 판단

    2. 내용 정제
       - 비속어 제거 또는 적절한 표현으로 대체
       - 맞춤법 및 문법 교정
       - 전문적이고 객관적인 톤으로 변환
       - '네','아니오' 같은 대답 표현은 제거
       - '동의합니다'로 통일해야 하는 표현 처리 (예: "저도 그래요", "맞아요" 등)

    3. 댓글 처리
       - 핵심 의견 추출
       - 중복 의견 제거
       - 객관적 톤으로 재작성

    4. 키워드 추출
       - 게시글당 3-5개의 핵심 키워드 선정
       - 상위 카테고리화가 가능한 포괄적 키워드 포함
       - 명사 형태의 키워드 선정

    # 출력 형식
    [번호]. [재작성된 게시글]
    댓글: 
    - [재작성된 댓글1]
    - [재작성된 댓글2]
    - [재작성된 댓글3]
    키워드:
    - [키워드1]
    - [키워드2]
    - [키워드3]
    성향: [경험성/질문성]

    # 세부 규칙

    게시글 재작성 규칙:
    1. 핵심 내용 유지하며 간결한 문체 사용
    2. 맞춤법과 문법 오류 교정
    3. 전문적이고 객관적인 톤 유지
    4. 비속어나 은어는 표준어로 대체
    5. 문장 끝에는 마침표 사용

    댓글 재작성 규칙:
    1. 핵심 의견만 추출하여 간단명료하게 정리
    2. 중복되는 의견은 하나로 통합
    3. 비속어 및 은어 제거
    4. 객관적 톤으로 변환
    5. 다중 의견은 번호로 구분하여 정리

    키워드 선정 기준:
    1. 주제를 대표하는 핵심 단어
    2. 상위 카테고리화 가능한 포괄적 용어
    3. 검색이나 분류에 유용한 단어
    4. 명사 형태로 통일
    5. 복합 명사의 경우 띄어쓰기 준수

    성향 판단 기준:
    - 경험성: 개인의 경험, 사례, 후기 등을 공유하는 내용
    - 질문성: 정보 요청, 조언 구하기, 의견 묻기 등의 내용

    # 주의사항
    1. 모든 게시글은 개별적으로 처리
    2. 원문의 핵심 의미는 반드시 유지
    3. 일관된 형식 준수
    4. 키워드는 각 게시글별로 독립적으로 추출
    5. 댓글이 없는 경우 "댓글: 없음" 으로 표시

    # 예시 입출력
    입력:
    1. Title: 업무 효율성 높이는 팁, Contents: 제가 일하면서 깨달은건데요 todo리스트 잘 쓰면 진짜 도움됨, Comments: ["완전 공감이요!", "저두요ㅋㅋ"]
    2. Title: 오늘 먹은 음식 추천해주세요, Contents: 저는 오늘 치킨 먹었어요 맛있어요, Comments: ["저도 치킨 먹었어요 맛있어요", "저도 치킨 먹었어요 맛있어요", "저는 치킨 별로"]
  
    출력:
    1. 업무 효율성을 높이기 위해 할 일 목록(Todo list)을 활용하는 것이 효과적이라는 경험을 공유합니다.
    댓글:
    - 동의합니다.
    키워드:
    - 업무 효율성
    - 할 일 목록
    - 업무 관리
    성향: 경험성

    2. 오늘 먹은 음식 추천해주세요
    댓글:
    - 많은 사람들이 치킨을 추천했습니다.
    - 일부 사람들은 치킨을 별로라고 표현했습니다.
    키워드:
    - 오늘 먹은 음식
    - 치킨
    성향: 경험성
    """
    
    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            functions=functions,
            function_call={"name": "process_posts"},
            max_tokens=8000,
            temperature=0.7,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=False
        )
        return response.choices[0].message.function_call.arguments
    except Exception as e:
        print(f"Error processing row {index}: {e}")
        return None

def process_csv(input_file, output_file):
    # CSV 파일 읽기
    df_input = pd.read_csv(input_file,
                encoding='utf-8',
                quotechar='"',  # 따옴표 문자 지정
                doublequote=True,  # 이중 따옴표 처리
                lineterminator='\n'  # 줄바꿈 문자 지정
                )

    # 새로운 DataFrame 생성
    df_output = pd.DataFrame(columns=['id', 'content', 'comments', 'keywords', 'tendency', 'views', 'date'])
              
    # 첫 번째 배치 전에 파일 생성
    df_output.to_csv(output_file, index=False, encoding='utf-8-sig')

    # 10개씩 배치 처리
    batch_size = 20
    for i in range(0, len(df_input), batch_size):
        batch_end = min(i + batch_size, len(df_input))
        print(f"Processing batch {i//batch_size + 1}: rows {i+1} to {batch_end}")
        
        # 배치의 입력 데이터 생성
        input_data = ""
        for j in range(i, batch_end):
            input_data += f"{j+1}. Title: {df_input.iloc[j]['Title']}, Contents: {df_input.iloc[j]['Contents']}, Comments: {df_input.iloc[j]['Comments']}\n"
        
        # GPT 처리
        result = process_text_with_gpt(input_data, i)
        if result:
            try:
                result_dict = json.loads(result)
                print(result_dict)
                # 배치의 각 게시글에 대해 처리
                for idx, post in enumerate(result_dict['posts']):
                    df_idx = i + idx
                    if df_idx >= len(df_input):
                        break
                    
                    df_output.at[df_idx, 'id'] = df_input.iloc[df_idx]['talkNo']
                    df_output.at[df_idx, 'content'] = post['content']
                    df_output.at[df_idx, 'comments'] = '; '.join(post['comments'])
                    df_output.at[df_idx, 'keywords'] = '; '.join(post['keywords'])
                    df_output.at[df_idx, 'tendency'] = post['tendency']
                    df_output.at[df_idx, 'views'] = df_input.iloc[df_idx]['ViewCount']
                    df_output.at[df_idx, 'date'] = df_input.iloc[df_idx]['Date']

                # 각 배치 처리 후 바로 파일에 저장
                df_output.to_csv(output_file, index=False, encoding='utf-8-sig')
                print(f"Processing complete. Results saved to {output_file}")

            except Exception as e:
                print(f"Error parsing GPT response for batch starting at row {i}: {e}")
        
        time.sleep(1)
    

# 사용 예시
input_file = 'crawling_result/crawling_combined_result.csv'   # 입력 CSV 파일 경로
output_file = 'refine_result/output3.csv'  # 출력 CSV 파일 경로

process_csv(input_file, output_file)