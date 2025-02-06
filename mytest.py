# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv  # 새로운 import 추가
import base64
from openai import AzureOpenAI  
import pandas as pd

# .env 파일 로드 추가
load_dotenv()

endpoint = os.getenv("ENDPOINT_URL", "https://jkht202502-de68d8a5-t00.openai.azure.com/")  
deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4o")  
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")  

# 키 기반 인증을 사용하여 Azure OpenAI Service 클라이언트 초기화    
client = AzureOpenAI(  
    azure_endpoint=endpoint,  
    api_key=subscription_key,  
    api_version="2024-05-01-preview",
)

# CSV 파일 전체를 데이터프레임으로 읽기
df = pd.read_csv('./crawling_results.csv', 
                 encoding='utf-8',
                 quotechar='"',  # 따옴표 문자 지정
                 doublequote=True,  # 이중 따옴표 처리
                 lineterminator='\n'  # 줄바꿈 문자 지정
                )

input_data = ''
# 한 줄씩 순회하기
for index, row in df.iterrows():
    print(row)
    if(index + 1 > 10):
        break
    title = row['Title']
    contents = row['Contents']
    input_data += f"{index+1}. Title: {title}, Contents: {contents}\n"

# IMAGE_PATH = "YOUR_IMAGE_PATH"
# encoded_image = base64.b64encode(open(IMAGE_PATH, 'rb').read()).decode('ascii')

#채팅 프롬프트 준비 
chat_prompt = [
    {
        "role": "system",
        "content": [
            {
                "type": "text",
                "text": "게시글의 타이틀과 내용을 기반으로 핵심 정보를 파악하고, 이를 분석하기 쉽도록 정제된 말투로 재작성합니다. 또한 게시글의 주요 키워드도 함께 추출하여 제공합니다.  \n\n# Steps  \n\n1. 게시글 타이틀과 내용을 확인하고, 주제 및 핵심 내용을 명확히 파악합니다.  \n2. 원문 내용과 동일한 의미를 유지하되 더 간결하고 분석하기 쉬운 문체로 게시글을 재작성합니다.  \n3. 게시글 안에서 주요 아이디어, 주제를 표현하는 핵심 키워드를 선정하고 추출합니다. \n4. 게시글은 각각은 번호로 매겨집니다. 번호별로 재작성된 게시글, 주요 키워드을 출력해야합니다.\n\n# Output 형식\n```markdown\n1. [번호]. [재작성된 게시글]\n   키워드:\n   - [키워드1]\n   - [키워드2]\n   - [키워드3]\n\n2. [번호]. [재작성된 게시글]\n   키워드:\n   - [키워드1]\n   - [키워드2]\n   - [키워드3]\n...\n\n10. [번호]. [재작성된 게시글]\n   키워드:\n   - [키워드1]\n   - [키워드2]\n   - [키워드3]\n```\n\n재작성 규칙:\n1. 각 게시글의 핵심 내용을 유지하되, 명확하고 간결한 문체로 재작성합니다.\n2. 맞춤법과 문법을 교정합니다.\n3. 전문적이고 객관적인 톤을 유지합니다.\n\n키워드 추출 규칙:\n1. 각 게시글의 주요 주제어를 3-5개 추출합니다.\n2. 명사 형태의 핵심 단어를 선정합니다.\n3. 게시글의 맥락을 대표할 수 있는 단어들을 선택합니다.\n\n중요: 각 게시글은 반드시 개별적으로 처리되어야 하며, 키워드도 각 게시글별로 별도로 추출되어야 합니다.\n\n# Examples  \n\n**Example Input:** \n```markdown\n1. Title: 일 잘하는 법: 시간 관리를 중심으로, Contents: 시간 관리는 제일 중요한 자기관리 스킬입니다. 저는 시간을 분 단위로 쪼개서 사용하는 방법으로 많은 일을 처리했습니다. 우선순위를 정하여 실천하는 것이 큰 도움을 줍니다. 이렇게 하면 효율적으로 하루를 보낼 수 있습니다.\n2. Title: 총무 및 경리 취업을 위한 자격증 추천 요청, Contents: 총무,경리 쪽으로취업하고싶은데요..자격증 어떤거 따는게 나을까요?간조,전산회계2급밖에없서여ㅠ\n```\n\n**Example Output:**  \n```markdown\n1. 시간 관리는 자기개발에서 핵심적인 역량입니다. 시간을 세밀하게 관리하고, 이를 통해 생산성을 극대화할 수 있습니다. 특히, 우선순위를 설정하고 이를 실천하는 방식은 하루를 효율적으로 활용하는 데 매우 유용합니다.  \n- 시간 관리\n- 자기관리\n- 우선순위\n- 생산성\n\n2. 총무나 경리 분야로 취업을 희망합니다. 현재 보유한 자격증은 간호조무사와 전산회계 2급입니다. 추가로 어떤 자격증을 취득하는 것이 좋을까요?  \n- 총무  \n- 경리  \n- 취업  \n- 자격증\n\n...\n\n10. 개인 카페에서 일한 지 5일째 되는 20대입니다. 사장님의 잔소리가 조금 있어서 위축되고 있습니다. 설날 기간에 급하게 고용된 것 같고, 커피에 대해 잘 모르고 손님도 적어 경험을 쌓기 힘듭니다. 오늘 실수로 얼린 망고를 떨어뜨렸습니다. 폐기해야 하는데 미처 버리지 못했습니다. 사장님께 혼날 것이 걱정입니다.  \n- 카페  \n- 실수  \n- 초보  \n- 고용 \n```  \n\n# Notes  \n\n- 불필요한 세부 사항은 제외하되, 정보의 본질이 손상되지 않도록 주의합니다.  \n- 문법 및 표현의 정확성을 철저히 검토합니다.  \n- 전문가의 입장에서 읽기 쉽고 분석하기 좋은 문체를 유지합니다. \n- output의 형식을 반드시 맞춰야합니다. 각 게시글의 키워드는 각각 추출되어야합니다."
            }
        ]
    }
] 

print(input_data)

# 음성이 사용되는 경우 음성 결과 포함  
messages = chat_prompt
    
# 완료 생성  
completion = client.chat.completions.create(  
    model=deployment,
    messages=messages,
    max_tokens=10000,  
    temperature=0.7,  
    top_p=0.95,  
    frequency_penalty=0,  
    presence_penalty=0,
    stop=None,  
    stream=False
)

print(completion.choices[0].message.content)  
    