from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import ssl
import chromedriver_autoinstaller
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import requests
import json
import time

# bs4 기본 설정
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

# 목록 페이지 URL
BASE_URL = 'https://www.albamon.com/alba-talk/experience'
TARGET_PAGE_URL = "https://www.albamon.com/alba-talk/experience?pageIndex={page}&searchKeyword=&sortType=CREATED_DATE"
TARGET_PAGE = 1330

# 크롤링 결과 저장용 리스트
post_data = []

'''
ChromeDriver Setting
'''
ssl._create_default_https_context = ssl._create_unverified_context  # SSL 인증서 검증 비활성화

# 자동으로 ChromeDriver 설치
chromedriver_autoinstaller.install()

# Selenium 실행 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--headless")  # 브라우저 창을 띄우지 않음
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Chrome WebDriver 실행
service = Service()
driver = webdriver.Chrome(service=service, options=chrome_options)


def get_soup(target_url, talkNo, headers):
    url = f'{target_url}/{talkNo}?sortType=CREATED_DATE'
    # 요청 및 BeautifulSoup 객체 생성
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup


def parse_comment_items(comment_list):
    # 날짜와 텍스트를 저장할 리스트
    comments_data = []
    for comment in comment_list:
        # 댓글 텍스트 추출
        comment_text_element = comment.select_one('.comment-list__text-override')
        comment_text = comment_text_element.get_text(strip=True) if comment_text_element else "N/A"

        # 데이터 딕셔너리에 저장
        comments_data.append(comment_text)
    return comments_data
    

'''
talkNo만 추출하기 위함
'''
def crawl_talk_no(pageIndex):
    print(f"🚀 페이지 {pageIndex} 크롤링 시작...")
    driver.get(TARGET_PAGE_URL.format(page=pageIndex))
    time.sleep(3)  # 페이지 로드 대기

    buttons = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".Button_button__S9rjD.Button_text__5x_Cn.Button_large___Kecx.tertiary")))
    
    # JavaScript를 이용해 클릭 (클릭 오류 방지)
    driver.execute_script("arguments[0].scrollIntoView();", buttons[0])
    driver.execute_script("arguments[0].click();", buttons[0])  

    time.sleep(2)  # 페이지 로드 대기
    # 현재 페이지 URL에서 talkNo 추출
    current_url = driver.current_url
    talk_no = current_url.split("/")[-1].split("?")[0]  # talkNo 추출
    print(f"🔹 게시글 URL: {current_url}")

    return talk_no


'''
최근 talkNo 부터 n개의 게시물 크롤링
'''
def crawl_post_detail(START_TALK_NO, LAST_TALK_NO):
    for talk_no in range(START_TALK_NO, LAST_TALK_NO, -1):
        soup = get_soup(BASE_URL, talk_no, headers)
        # 덧글 저장 리스트
        parsed_comments = []

        # 콘텐츠 영역 (게시글 제목, 내용, 작성일자)
        title_element = soup.select_one('.DetailTitle_detail__header--title__Bbp40')
        content_element = soup.select_one('.Detail_content__content__hJ5M7')
        date_element = soup.select_one('.CommonInfos_info__wrapper__aGcEl > div:nth-child(2)')
        view_count_element = soup.select_one('.experience__span--view')

        title = title_element.get_text(strip=True) if title_element else "N/A"
        contents = content_element.get_text(strip=True) if content_element else "N/A"
        content_date = date_element.get_text(strip=True) if date_element else "N/A"
        view_count = view_count_element.get_text(strip=True) if date_element else "N/A"
        # 필수값이 없거나 빈 문자열이면 저장하지 않고 넘어가기
        if not title_element or not title_element.get_text(strip=True) or not contents or not content_date:
            continue


        # 댓글 리스트 파싱
        comment_list = soup.select('.CommentList_comment-contents__YVrtF > ul li')
        parsed_comments = parse_comment_items(comment_list)

        # 게시글 데이터를 리스트에 추가
        post_data.append({
            "talkNo": talk_no,
            "Title": title,
            "Contents": contents,
            "Date": content_date,
            "ViewCount": view_count,
            "Comments": parsed_comments
        })

        print(f"talkNo: {talk_no}")
        print(f"Title: {title}")
        print(f"Contents: {contents}")
        print(f"Date: {content_date}")
        print(f"comments : {parsed_comments}")
        print(f"ViewCount: {view_count}")
        print("-" * 80)

    return post_data
    

START_TALK_NO = int(crawl_talk_no(1))
LAST_TALK_NO = int(crawl_talk_no(TARGET_PAGE))

data = crawl_post_detail(START_TALK_NO, LAST_TALK_NO)

# 브라우저 종료
driver.quit()

# 데이터프레임 생성
df = pd.DataFrame(data)
# 저장할 디렉토리 생성
output_dir = "crawling_result"
os.makedirs(output_dir, exist_ok=True)


# CSV 파일로 저장
csv_file =  os.path.join(output_dir, "crawling_combined_result.csv")
df.to_csv(csv_file, index=False, encoding='utf-8-sig')  # UTF-8 인코딩으로 저장
print(f"Data saved to {csv_file}")