from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import chromedriver_autoinstaller
import ssl
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# bs4 기본 설정
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

def get_soup(url, headers):
    # 요청 및 BeautifulSoup 객체 생성
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

# ✅ **댓글 크롤링하는 함수**
def get_comments_from_page(comment_list):
    # 날짜와 텍스트를 저장할 리스트
    comments_data = []
    for comment in comment_list:
        # 댓글 텍스트 추출
        comment_text_element = comment.select_one('.comment-list__text-override')
        comment_text = comment_text_element.get_text(strip=True) if comment_text_element else "N/A"

        # 데이터 딕셔너리에 저장
        comments_data.append(comment_text)
    return comments_data





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

# 목록 페이지 URL
base_url = "https://www.albamon.com/alba-talk/experience?pageIndex={page}&searchKeyword=&sortType=CREATED_DATE"

# 버튼 클릭 후 상세 페이지 크롤링
def crawl_experience(endPageIndex):
    results = []
    for page in range(1, endPageIndex+1):  
        print(f"🚀 페이지 {page} 크롤링 시작...")
        driver.get(base_url.format(page=page))  # 페이지 이동
        time.sleep(3)  # 페이지 로드 대기
    
        # ✅ 버튼 리스트 가져오기 (게시글 목록)
        # buttons = driver.find_elements(By.CSS_SELECTOR, ".Button_button__S9rjD.Button_text__5x_Cn.Button_large___Kecx.tertiary")

         # 버튼이 로드될 때까지 기다림
        try:
            buttons = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".Button_button__S9rjD.Button_text__5x_Cn.Button_large___Kecx.tertiary"))                )
        except:
            print(f"⚠️ 페이지 {page}에서 버튼을 찾을 수 없습니다. 다음 페이지로 이동합니다.")
            continue  # 다음 페이지로 이동
        
        for i in range(len(buttons)):  # 각 버튼 클릭
            if i >= len(buttons):
                print(f"⚠️ {i}번째 버튼이 없습니다. 리스트 길이: {len(buttons)}")
                break

            # JavaScript를 이용해 클릭 (클릭 오류 방지)
            driver.execute_script("arguments[0].scrollIntoView();", buttons[i])
            driver.execute_script("arguments[0].click();", buttons[i])  # JavaScript 클릭 사용

            time.sleep(2)  # 페이지 로드 대기

            # 현재 페이지 URL에서 talkNo 추출
            current_url = driver.current_url
            talk_no = current_url.split("/")[-1].split("?")[0]  # talkNo 추출
            print(f"🔹 게시글 URL: {current_url}")

            # ✅ BeautifulSoup으로 페이지 파싱
            soup = get_soup(current_url, headers)

            # 상세 페이지에서 제목, 내용, 날짜 크롤링
            try:
                # 콘텐츠 영역 (게시글 제목, 내용, 작성일자)
                title_element = soup.select_one('.DetailTitle_detail__header--title__Bbp40')
                contents_element = soup.select_one('.Detail_content__content__hJ5M7')
                date_element = soup.select_one('.CommonInfos_info__wrapper__aGcEl > div:nth-child(2)')
                view_count_element = soup.select_one('.experience__span--view')

                title = title_element.get_text(strip=True) if title_element else "N/A"
                contents = contents_element.get_text(strip=True) if contents_element else "N/A"
                date = date_element.get_text(strip=True) if date_element else "N/A"
                view_count = view_count_element.get_text(strip=True) if date_element else "N/A"

                # 필수값이 없거나 빈 문자열이면 저장하지 않고 넘어가기
                if not title_element or not title_element.get_text(strip=True) or not contents or not date:
                    continue

                # 댓글 리스트 파싱
                comment_list = soup.select('.CommentList_comment-contents__YVrtF > ul li')
                parsed_comments = get_comments_from_page(comment_list)
                
                # 데이터 저장
                results.append({
                    "talkNo": talk_no,
                    "Title": title,
                    "Contents": contents,
                    "Date": date,
                    "ViewCount": view_count,
                    "Comments": parsed_comments
                })

                print(f"talkNo: {talk_no}")
                print(f"Title: {title}")
                print(f"Contents: {contents}")
                print(f"Date: {date}")
                print(f"comments : {parsed_comments}")
                print(f"ViewCount: {view_count}")
                print("-" * 80)

            except Exception as e:
                print(f"❌ 데이터 크롤링 실패: {e}")

            # 뒤로 가기
            driver.back()
            time.sleep(2)

            # 다시 버튼 리스트 가져오기
            buttons = driver.find_elements(By.CSS_SELECTOR, ".Button_button__S9rjD.Button_text__5x_Cn.Button_large___Kecx.tertiary")


    return results

# 크롤링 실행
data = crawl_experience(1330)

# 브라우저 종료
driver.quit()

# 데이터프레임 생성
df = pd.DataFrame(data)
# 저장할 디렉토리 생성
output_dir = "crawling_result"
os.makedirs(output_dir, exist_ok=True)

# CSV 파일로 저장
csv_file =  os.path.join(output_dir, "crawling_detail_result.csv")
df.to_csv(csv_file, index=False, encoding='utf-8-sig')  # UTF-8 인코딩으로 저장
print(f"Data saved to {csv_file}")