import pandas as pd
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import time

# .env 파일 로드
load_dotenv()

endpoint = os.getenv("ENDPOINT_URL", "https://jkht202502-de68d8a5-t00.openai.azure.com/")  
deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4o")  
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")  

# Azure OpenAI 설정
client = AzureOpenAI(
    azure_endpoint=endpoint,  
    api_key=subscription_key,  
    api_version="2024-05-01-preview",
)

def process_text_with_gpt(prompt, index):
    system_prompt = """
    게시글의 타이틀과 내용을 기반으로 핵심 정보를 파악하고, 이를 분석하기 쉽도록 정제된 말투로 재작성합니다. 또한 게시글의 주요 키워드도 함께 추출하여 제공합니다.  

    # Steps  

    1. 게시글 타이틀과 내용을 확인하고, 주제 및 핵심 내용을 명확히 파악합니다.  
    2. 원문 내용과 동일한 의미를 유지하되 더 간결하고 분석하기 쉬운 문체로 게시글을 재작성합니다.  
    3. 게시글 안에서 주요 아이디어, 주제를 표현하는 핵심 키워드를 선정하고 추출합니다. 
    4. 게시글은 각각은 번호로 매겨집니다. 번호별로 재작성된 게시글, 주요 키워드을 출력해야합니다.

    # 다음 게시글들을 분석하여 각각의 게시글에 대해 아래 형식으로 출력해주세요.

    출력 형식:
    1. [번호]. [재작성된 게시글]
    키워드:
    - [키워드1]
    - [키워드2]
    - [키워드3]

    2. [번호]. [재작성된 게시글]
    키워드:
    - [키워드1]
    - [키워드2]
    - [키워드3]

    (이하 계속...)

    재작성 규칙:
    1. 각 게시글의 핵심 내용을 유지하되, 명확하고 간결한 문체로 재작성합니다.
    2. 맞춤법과 문법을 교정합니다.
    3. 전문적이고 객관적인 톤을 유지합니다.

    키워드 추출 규칙:
    1. 각 게시글의 주요 주제어를 3-5개 추출합니다.
    2. 명사 형태의 핵심 단어를 선정합니다.
    3. 게시글의 맥락을 대표할 수 있는 단어들을 선택합니다.

    중요: 각 게시글은 반드시 개별적으로 처리되어야 하며, 키워드도 각 게시글별로 별도로 추출되어야 합니다.

    # Examples  

    **Example Input:**  
    1. Title: 일 잘하는 법: 시간 관리를 중심으로, Contents: 시간 관리는 제일 중요한 자기관리 스킬입니다. 저는 시간을 분 단위로 쪼개서 사용하는 방법으로 많은 일을 처리했습니다. 우선순위를 정하여 실천하는 것이 큰 도움을 줍니다. 이렇게 하면 효율적으로 하루를 보낼 수 있습니다.
    2. Title: 총무 및 경리 취업을 위한 자격증 추천 요청, Contents: 총무,경리 쪽으로취업하고싶은데요..자격증 어떤거 따는게 나을까요?간조,전산회계2급밖에없서여ㅠ

    **Example Output:**  
    ```markdown
    1. 시간 관리는 자기개발에서 핵심적인 역량입니다. 시간을 세밀하게 관리하고, 이를 통해 생산성을 극대화할 수 있습니다. 특히, 우선순위를 설정하고 이를 실천하는 방식은 하루를 효율적으로 활용하는 데 매우 유용합니다.  
    - 시간 관리
    - 자기관리
    - 우선순위
    - 생산성

    2. 총무나 경리 분야로 취업을 희망합니다. 현재 보유한 자격증은 간호조무사와 전산회계 2급입니다. 추가로 어떤 자격증을 취득하는 것이 좋을까요?  
    - 총무  
    - 경리  
    - 취업  
    - 자격증  
    ```  

    # Notes  

    - 불필요한 세부 사항은 제외하되, 정보의 본질이 손상되지 않도록 주의합니다.  
    - 문법 및 표현의 정확성을 철저히 검토합니다.  
    - 전문가의 입장에서 읽기 쉽고 분석하기 좋은 문체를 유지합니다. 
    - output의 형식을 반드시 맞춰야합니다. 각 게시글의 키워드는 각각 추출되어야합니다.
    """
    
    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=5000,
            temperature=0.7,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error processing row {index}: {e}")
        return None

def process_csv(input_file, output_file):
    # CSV 파일 읽기
    df = pd.read_csv(input_file,
                encoding='utf-8',
                quotechar='"',  # 따옴표 문자 지정
                doublequote=True,  # 이중 따옴표 처리
                lineterminator='\n'  # 줄바꿈 문자 지정
                )
    
    # 결과를 저장할 새로운 컬럼 생성
    df['processed_content'] = ''
    df['keywords'] = ''

    # 첫 번째 배치 전에 파일 생성
    df.to_csv(output_file, index=False, encoding='utf-8-sig')

    # 
    # Processing batch 64: rows 631 to 640 부터 시작해야함
    # 10개씩 배치 처리
    batch_size = 10
    for i in range(0, len(df), batch_size):
        batch_end = min(i + batch_size, len(df))
        print(f"Processing batch {i//batch_size + 1}: rows {i+1} to {batch_end}")
        
        # 배치의 입력 데이터 생성
        input_data = ""
        for j in range(i, batch_end):
            input_data += f"{j+1}. Title: {df.iloc[j]['Title']}, Contents: {df.iloc[j]['Contents']}\n"
        
        # GPT 처리
        result = process_text_with_gpt(input_data, i)
        print(result)
        
        if result:
            # 각 항목별로 결과 파싱
            try:
                # 번호로 결과 분리
                entries = result.split('\n\n')
                for entry_idx, entry in enumerate(entries):
                    if not entry.strip():
                        continue
                    
                    df_idx = i + entry_idx
                    if df_idx >= len(df):
                        break
                        
                    # 내용과 키워드 분리
                    parts = entry.split('키워드:')
                    if len(parts) == 2:
                        content_part = parts[0].strip()
                        # 번호 제거 (예: "1. " 제거)
                        content_part = '.'.join(content_part.split('.')[1:]).strip()
                        keywords_part = parts[1].strip()
                        
                        df.at[df_idx, 'processed_content'] = content_part
                        df.at[df_idx, 'keywords'] = keywords_part
                
                # 각 배치 처리 후 바로 파일에 저장
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                print(f"Processing complete. Results saved to {output_file}")

            except Exception as e:
                print(f"Error parsing GPT response for batch starting at row {i}: {e}")
        
        # API 호출 제한을 위한 대기
        time.sleep(1)
    

# 사용 예시
input_file = 'crawling_results.csv'  # 입력 CSV 파일 경로
output_file = 'output.csv'  # 출력 CSV 파일 경로

process_csv(input_file, output_file)