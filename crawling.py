import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os

TARGET_URL = 'https://www.albamon.com/alba-talk/experience'
 
 # 헤더와 요청
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
# data = requests.get(TARGET_URL, headers=headers)
# soup = BeautifulSoup(data.text, 'html.parser')


def fetch_page_data(target_url, page, headers):
    url = f'{target_url}?pageIndex={page}&searchKeyword=&sortType=CREATED_DATE'
    # 요청 및 BeautifulSoup 객체 생성
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def convert_date(date_text):
    now = datetime.now()
    if "분전" in date_text or "시간전" in date_text:
        # "몇 분 전", "몇 시간 전"은 오늘 날짜로 처리
        return now.strftime("%Y-%m-%d")
    else:
        return date_text


def parse_items(common_list):
    # 데이터를 추출하여 딕셔너리 형태로 반환
    data = []
    for item in common_list:
        title = item.select_one('.title > div')
        contents = item.select_one('.contents > div')
        date = item.select_one('.CommonInfos_info__wrapper__aGcEl > div:nth-child(2)')

        # 날짜 변환
        raw_date = date.text.strip() if date else "N/A"
        converted_date = convert_date(raw_date)

        # 텍스트만 출력
        print("Title:", title.text.strip() if title else "N/A")
        print("Contents:", contents.text.strip() if contents else "N/A")
        print("Date:", converted_date)
        print("-" * 80)

        # 데이터 딕셔너리에 저장
        data.append({
            "Title": title.text.strip() if title else "N/A",
            "Contents": contents.text.strip() if contents else "N/A",
            "Date": converted_date
        })
    return data




# 크롤링 결과 저장용 리스트
all_data = []


# 1페이지부터 10페이지까지 크롤링
for page in range(1, 11):
    print(f"Crawling page {page}")
    soup = fetch_page_data(TARGET_URL, page, headers)
    
    # 공통 리스트 선택
    common_list = soup.select('.CommonList_wrapper__padding__CP_Jc')

    page_data = parse_items(common_list)
    all_data.extend(page_data)


# DataFrame 생성
df = pd.DataFrame(all_data)

# 저장할 디렉토리 생성
output_dir = "crawling_result"
os.makedirs(output_dir, exist_ok=True)

# CSV 파일로 저장
csv_file = os.path.join(output_dir, "crawling_results.csv")
df.to_csv(csv_file, index=False, encoding='utf-8-sig')
print(f"Data saved to {csv_file}")
