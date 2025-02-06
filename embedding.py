import os
import re
import pandas as pd
import numpy as np
import tiktoken
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key        = os.getenv("AZURE_OPENAI_API_KEY"),
    api_version    = os.getenv("OPENAI_API_VERSION")
)

deployment_name = os.getenv("DEPLOYMENT_NAME")
deployment_embedding_name = os.getenv("DEPLOYMENT_EMBEDDING_NAME")

input_file = './categorized_output_sample.csv'   # 입력 CSV 파일 경로
output_file = './categorized_output_sample_embeddings_3_large.csv'  # 출력 CSV 파일 경로

# df=pd.read_csv(os.path.join(os.getcwd(),input_file)) 
df=pd.read_csv(os.path.join(os.getcwd(), input_file))

print(df)

# s is input text
def normalize_text(s, sep_token = " \n "):
    s = re.sub(r'\s+',  ' ', s).strip()
    s = re.sub(r". ,","",s)
    # remove all instances of multiple spaces
    s = s.replace("..",".")
    s = s.replace(". .",".")
    s = s.replace("\n", "")
    s = s.strip()
    
    return s

def generate_embeddings(text, model=deployment_embedding_name):
    return client.embeddings.create(input = [text], model=model).data[0].embedding

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_embedding(text, model=deployment_embedding_name): # model = "deployment_name"
    return client.embeddings.create(input = [text], model=model).data[0].embedding

def search_docs(df, user_query, top_n=3, to_print=True):
    embedding = get_embedding(
        user_query,
        model=deployment_embedding_name # model should be set to the deployment name you chose when you deployed the text-embedding-ada-002 (Version 2) model
    )
    df["similarities"] = df.content_vector.apply(lambda x: cosine_similarity(x, embedding))

    res = (
        df.sort_values("similarities", ascending=False)
        .head(top_n)
    )
    if to_print:
        print(res)
    return res

# 사용자 질의에 대하여 RAG 기반의 답변을 생성하는 함수
def generate_rag_answer(df, user_query, top_n=3, ):
    content_msg = ""
    res = search_docs(df, user_query, top_n=top_n, to_print=False)
    print(res)
    for index, result in res.iterrows():
        content_msg = content_msg + "id:"+ str(result.id) + ", 내용:"+ result.content + ", 답변:" + result.comments + "  \n"
    system_msg = """
    You should generate an answer based on the
    "### Grouding data" message provided below, rather than using any knowledge you have about the user's question.
    \n\n### Grouding data  \n""" + content_msg
    
    system_msg += """### Notes\n세 가지의 Grounding data를 조합해서 가장 좋은 답변을 도출해줘.\n해당 데이터의 id도 같이 출력해줘.
    """
    
    #     # If there is no "### Grouding data" message, "I could not find a context for the answer." You have to answer. 
    print(content_msg)

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_query},
        ],
        temperature=0.1,
        max_tokens=2000
    )

    return response.choices[0].message.content

def process_embedding(input_file, output_file):
    # 파일에서 데이터 읽기
    df = pd.read_csv(os.path.join(os.getcwd(), input_file))
    pd.options.mode.chained_assignment = None
    
    df['content'] = df["content"].apply(lambda x : normalize_text(x))

    ## Azure OpenAI에서 제공하는 Embedding API를 활용하기 위해 문서에서 Text 길이가 8,192 토큰이 넘지 않는 문서를 확인
    tokenizer = tiktoken.get_encoding("cl100k_base")
    df['n_tokens'] = df["content"].apply(lambda x: len(tokenizer.encode(x)))
    df = df[df.n_tokens<8192]

    ## 문서의 Text에서 각각의 토큰별로 나뉘어진 부분 확인
    sample_encode = tokenizer.encode(df.content[0]) 
    decode = tokenizer.decode_tokens_bytes(sample_encode)
    # model should be set to the deployment name you chose when you deployed the text-embedding-ada-002 (Version 2) model
    # content_vector는 예약어 아님
    df['content_vector'] = df["content"].apply(lambda x : generate_embeddings (x, model = deployment_embedding_name)) 
    df.to_csv(os.path.join(os.getcwd(), output_file), index=False)
    print(df)

    ## 유사도 관계를 파악하기 위해서 질의에 대한 결과 분석
    res = search_docs(df, "부스 판매 알바를 하고 싶은데 초보자가 하기에 괜찮을까요?", top_n=4)
    print(res)
    res = search_docs(df, "알바를 구했는데 연락이 오지 않아요.", top_n=4)
    print(res)
    res = search_docs(df, "3.3% 소득세 공제가 고용 기록에 남는데 왜 그런걸까요?", top_n=4)
    print(res)

    # 사용자 질의에 대하여 RAG 기반의 답변을 생성
    user_query = """알바를 구했는데 연락이 오지 않아요."""
    # user_query = """자동차의 역사를 설명해줘."""
    response = generate_rag_answer(df, user_query)
    print("답변: " + response)

process_embedding(input_file, output_file)