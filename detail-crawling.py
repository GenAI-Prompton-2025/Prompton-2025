from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


TARGET_URL = "https://www.albamon.com/alba-talk/experience"

# Update the driver initialization
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

driver.get(TARGET_URL)

# 페이지 로드 대기
driver.implicitly_wait(10)



# 모든 버튼 요소 찾기
buttons = driver.find_elements(By.CLASS_NAME, "Button_button__S9rjD")

print(len(buttons))


# 브라우저 종료
driver.quit()
