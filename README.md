# 크롤링 데이터 후처리 프로젝트

## 프로젝트 개요

이 프로젝트는 크롤링된 데이터를 Azure OpenAI GPT를 사용하여 후처리하는 파이썬 기반 애플리케이션입니다.

## 주요 기능

- CSV 파일의 크롤링 데이터 읽기
- Azure OpenAI GPT를 활용한 텍스트 처리
- 처리된 결과를 새로운 CSV 파일로 저장

## 설치 방법

1. 필요한 패키지 설치:

```bash
pip install -r requirements.txt
```

## 환경 설정

`.env` 파일을 생성하고 다음 환경 변수를 설정하세요:

```plaintext
ENDPOINT_URL=your_azure_endpoint
DEPLOYMENT_NAME=your_deployment_name
AZURE_OPENAI_API_KEY=your_api_key
```

## 사용 방법

1. 크롤링된 데이터를 CSV 파일로 준비합니다.
2. `csv_post_processor.py`를 실행하여 데이터 처리:

```python
python csv_post_processor.py
```

## 파일 구조

- `mytest.py`: Azure OpenAI 연동 테스트 파일
- `csv_post_processor.py`: 메인 처리 스크립트
- `requirements.txt`: 필요한 패키지 목록

## 주의사항

- API 호출 제한을 고려하여 처리 간격을 1초로 설정했습니다.
- 현재는 테스트를 위해 처음 10개의 행만 처리하도록 설정되어 있습니다.

## 의존성

- Python 3.x
- OpenAI >= 1.12.0
- Pandas >= 2.0.0
- python-dotenv >= 1.0.0

## 라이선스

MIT License
