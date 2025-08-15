# HTTP Request - Home Assistant 커스텀 통합

[![GitHub](https://img.shields.io/github/license/pageskr/ha-http-request)](https://github.com/pageskr/ha-http-request/blob/main/LICENSE)
[![GitHub release](https://img.shields.io/github/release/pageskr/ha-http-request.svg)](https://github.com/pageskr/ha-http-request/releases)

HTTP Request 통합은 HTTP 요청을 통해 외부 API나 웹 페이지에서 데이터를 가져와 Home Assistant 센서로 만들어주는 기능을 제공합니다.

제작: **Pages in Korea (pages.kr)**

## 주요 기능

- 🌐 다양한 HTTP 메소드 지원 (GET, POST, PUT, PATCH, DELETE)
- 📊 JSON, HTML, 텍스트 응답 파싱
- 🎯 JMESPath, CSS Selector, 정규식을 통한 데이터 추출
- 📝 Jinja2 템플릿을 사용한 값 변환
- 🔄 사용자 정의 갱신 주기
- 🏠 Home Assistant 기기 정보 통합
- 🌍 다국어 지원 (한국어, 영어)

## 설치 방법

### HACS를 통한 설치 (권장)
1. HACS에서 사용자 정의 저장소 추가
   - 메뉴 → 사용자 정의 저장소
   - URL: `https://github.com/pageskr/ha-http-request`
   - 카테고리: 통합
2. HACS에서 "HTTP Request" 검색 후 설치
3. Home Assistant 재시작

### 수동 설치
1. [최신 릴리즈](https://github.com/pageskr/ha-http-request/releases)에서 소스 코드 다운로드
2. `custom_components/http_request` 폴더를 Home Assistant의 `custom_components` 디렉토리에 복사
3. Home Assistant 재시작

## 설정 방법

### 통합 추가
1. 설정 → 기기 및 서비스 → 통합 추가
2. "HTTP Request" 검색
3. 센서 설정 입력

### 설정 항목

#### 기본 설정
| 항목 | 설명 | 필수 | 기본값 |
|------|------|------|--------|
| 센서 이름 | 생성될 센서의 이름 | ✓ | - |
| HTTP 메소드 | GET, POST, PUT, PATCH, DELETE | ✓ | GET |
| URL | 요청할 URL 주소 | ✓ | - |
| 헤더 | HTTP 헤더 (JSON 형식) | | {} |
| 파라미터 | URL 파라미터 (JSON 형식) | | {} |
| 본문 | 요청 본문 (JSON 형식) | | {} |
| 타임아웃 | 응답 대기 시간 (초) | | 15 |
| SSL 검증 | SSL 인증서 검증 여부 | | true |
| 갱신 주기 | 데이터 갱신 주기 (초) | | 60 |

#### 파싱 설정
| 항목 | 설명 | 응답 타입 |
|------|------|-----------|
| 응답 타입 | json, html, text 중 선택 | 모두 |
| JMESPath | JSON 데이터 추출 경로 | json |
| CSS 선택자 | HTML 요소 선택자 | html |
| HTML 속성 | 추출할 속성 (text 또는 속성명) | html |
| 정규식 | 텍스트 추출 패턴 | text |
| 그룹 번호 | 정규식 캡처 그룹 | text |

#### 템플릿 설정
| 항목 | 설명 |
|------|------|
| 값 템플릿 | 센서 상태값을 변환하는 Jinja2 템플릿 |

### 템플릿 변수

템플릿에서 사용 가능한 변수:
- `value`: 파싱된 원본 값
- `json`: JSON 응답 전체 (json 타입인 경우)
- `text`: 텍스트 응답 전체
- `status`: HTTP 상태 코드

## 사용 예시

### 1. JSON API - 날씨 정보
```yaml
이름: 현재 온도
URL: https://api.openweathermap.org/data/2.5/weather?q=Seoul&appid=YOUR_API_KEY
응답 타입: json
JMESPath: main.temp
값 템플릿: {{ (value - 273.15) | round(1) }}
```

### 2. HTML 스크래핑 - 제품 가격
```yaml
이름: 제품 가격
URL: https://example.com/product/123
응답 타입: html
CSS 선택자: span.price
HTML 속성: text
값 템플릿: {{ value | replace(',', '') | int }}
```

### 3. 텍스트 파싱 - 서버 상태
```yaml
이름: 서버 CPU 사용률
URL: https://example.com/server/status.txt
응답 타입: text
정규식: CPU:\s*(\d+)%
그룹 번호: 1
```

### 4. 추가 속성 설정
```json
[
  {
    "key": "humidity",
    "response_type": "json",
    "json_jmes": "main.humidity",
    "attr_template": "{{ value }}%"
  },
  {
    "key": "last_update",
    "response_type": "html",
    "html_selector": "span.update-time",
    "html_attr": "text"
  }
]
```

## 고급 사용법

### 헤더에 인증 토큰 추가
```json
{
  "Authorization": "Bearer YOUR_TOKEN",
  "Content-Type": "application/json"
}
```

### POST 요청 본문
```json
{
  "query": "temperature",
  "location": "Seoul"
}
```

### 복잡한 템플릿 예시
```jinja2
{% if value > 30 %}
  높음
{% elif value > 20 %}
  보통
{% else %}
  낮음
{% endif %}
```

## 문제 해결

### 센서가 "unavailable" 상태인 경우
1. URL이 올바른지 확인
2. 네트워크 연결 확인
3. SSL 인증서 문제시 `SSL 검증`을 false로 설정
4. 타임아웃 값 증가
5. Home Assistant 로그 확인

### 파싱 오류
1. JMESPath/CSS Selector/정규식 문법 확인
2. 응답 형식이 예상과 일치하는지 확인
3. `http_status` 속성으로 HTTP 상태 코드 확인

## 보안 주의사항

⚠️ **중요**: API 키나 인증 토큰은 반드시 `secrets.yaml`에 저장하고 참조하세요.

```yaml
# secrets.yaml
weather_api_key: YOUR_ACTUAL_API_KEY

# 통합 설정시
URL: https://api.openweathermap.org/data/2.5/weather?q=Seoul&appid=!secret weather_api_key
```

## 기여하기

버그 리포트, 기능 제안, 풀 리퀘스트는 [GitHub](https://github.com/pageskr/ha-http-request)에서 환영합니다.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](https://github.com/pageskr/ha-http-request/blob/main/LICENSE) 파일을 참조하세요.

## 제작자

**Pages in Korea (pages.kr)**
- 웹사이트: [https://pages.kr](https://pages.kr)
- GitHub: [@pageskr](https://github.com/pageskr)