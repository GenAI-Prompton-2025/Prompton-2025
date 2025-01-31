import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import json

TARGET_URL = 'https://www.albamon.com/alba-talk/experience'
SART_TALK_NO = 978459
 
 # 헤더와 요청
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

def fetch_data(target_url, talkNo, headers):
    url = f'{target_url}/{talkNo}?sortType=CREATED_DATE'
    # 요청 및 BeautifulSoup 객체 생성
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup



def parse_comment_items(comment_list):
    # 날짜와 텍스트를 저장할 리스트
    comments_data = []
    for comment in comment_list:
        # 날짜 추출
        comment_date_element = comment.select_one('.comment-list__detail-override')
        comment_date = comment_date_element.get_text(strip=True) if comment_date_element else "N/A"

        # 댓글 텍스트 추출
        comment_text_element = comment.select_one('.comment-list__text-override')
        comment_text = comment_text_element.get_text(strip=True) if comment_text_element else "N/A"

        # 데이터 딕셔너리에 저장
        comments_data.append({"comment_date": comment_date, "comment_text": comment_text})
    return comments_data



# 크롤링 결과 저장용 리스트
post_data = []  # 게시글 데이터
comment_data = []  # 댓글 데이터

# 최근 talkNo 부터 n개의 게시물 크롤링
for talkNo in range(SART_TALK_NO, SART_TALK_NO-100, -1):
    soup = fetch_data(TARGET_URL, talkNo, headers)
    # 덧글 저장 리스트
    parsed_comments = []

     # 콘텐츠 영역 (게시글 제목, 내용, 작성일자)
    title_element = soup.select_one('.DetailTitle_detail__header--title__Bbp40')
    content_element = soup.select_one('.Detail_content__content__hJ5M7')
    date_element = soup.select_one('.CommonInfos_info__wrapper__aGcEl > div:nth-child(2)')

    title = title_element.get_text(strip=True) if title_element else "N/A"
    content = content_element.get_text(strip=True) if content_element else "N/A"
    content_date = date_element.get_text(strip=True) if date_element else "N/A"

    # 필수값이 없거나 빈 문자열이면 저장하지 않고 넘어가기
    if not title_element or not title_element.get_text(strip=True) or not content or not content_date:
        continue

    

    # 댓글 리스트 파싱
    comment_list = soup.select('.CommentList_comment-contents__YVrtF > ul li')
    parsed_comments = parse_comment_items(comment_list)

    # 게시글 데이터를 리스트에 추가
    post_data.append({
        "talkNo": talkNo,
        "title": title,
        "content": content,
        "content_date": content_date,
        "comments": json.dumps(parsed_comments, ensure_ascii=False)
    })

    
    print(f"✅ Saved talkNo {talkNo}")


# 데이터프레임 생성
df_posts = pd.DataFrame(post_data)
# df_comments = pd.DataFrame(comment_data)

# **게시글 데이터와 댓글 데이터를 talkNo를 기준으로 병합**
# merged_data = pd.merge(df_posts, df_comments, on="talkNo", how="inner")


# 저장할 디렉토리 생성
output_dir = "crawling_result"
os.makedirs(output_dir, exist_ok=True)

# CSV 파일로 저장
csv_file =  os.path.join(output_dir, "crawling_detail_results_array.csv")
df_posts.to_csv(csv_file, index=False, encoding='utf-8-sig')  # UTF-8 인코딩으로 저장
print(f"Data saved to {csv_file}")