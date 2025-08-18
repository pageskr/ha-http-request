# HTTP Request - Home Assistant 커스텀 통합

[![GitHub](https://img.shields.io/github/license/pageskr/ha-http-request)](https://github.com/pageskr/ha-http-request/blob/main/LICENSE)
[![GitHub release](https://img.shields.io/github/release/pageskr/ha-http-request.svg)](https://github.com/pageskr/ha-http-request/releases)

HTTP 요청을 통해 외부 API나 웹 페이지에서 데이터를 가져와 Home Assistant 센서로 만들어주는 통합입니다.

제작: **Pages in Korea (pages.kr)**  
GitHub: [https://github.com/pageskr/ha-http-request](https://github.com/pageskr/ha-http-request)

## 주요 기능

- 🌐 **다양한 HTTP 메소드 지원**: GET, POST, PUT, DELETE, PATCH
- 📊 **세 가지 응답 형식 파싱**:
  - **JSON**: JSON 경로를 사용한 데이터 추출
  - **HTML**: CSS Selector를 사용한 요소 선택
  - **Text**: 정규식을 사용한 패턴 매칭
- 🎯 **Jinja2 템플릿 지원**: 센서 값을 동적으로 변환
- 🔧 **유연한 설정**: 헤더, 파라미터, 본문, 타임아웃, SSL 옵션
- 🏠 **Home Assistant 기기 통합**: 센서가 기기로 그룹화되어 관리 용이
- 🌍 **다국어 지원**: 한국어, 영어

## 설치 방법

### 수동 설치
1. `custom_components/http_request` 폴더를 Home Assistant의 `custom_components` 디렉토리에 복사
2. Home Assistant 재시작
3. 설정 → 기기 및 서비스 → 통합 추가 → "HTTP Request" 검색

## 사용 방법

### 1단계: 기본 설정
통합 추가 시 다음 정보를 입력합니다:

| 항목 | 설명 | 예시 |
|------|------|------|
| **이름** | 센서 이름 | 날씨 정보 |
| **URL** | 데이터를 가져올 URL | https://api.example.com/data |
| **HTTP 메소드** | 요청 방식 | GET |
| **응답 타입** | 응답 형식 | json, html, text |
| **헤더** | HTTP 헤더 (JSON) | {"Authorization": "Bearer TOKEN"} |
| **URL 파라미터** | 쿼리 파라미터 (JSON) | {"city": "Seoul", "units": "metric"} |
| **요청 본문** | POST/PUT 본문 (JSON) | {"query": "temperature"} |
| **타임아웃** | 응답 대기 시간 | 30 |
| **SSL 검증** | SSL 인증서 검증 | true |
| **업데이트 간격** | 데이터 갱신 주기 | 300 |

### 2단계: 파싱 설정
선택한 응답 타입에 따라 파싱 옵션이 표시됩니다:

#### JSON 응답
- **JSON 경로**: 데이터 추출 경로 (예: `data.temperature`, `items[0].value`)
- **값 템플릿**: Jinja2 템플릿 (선택사항)

#### HTML 응답
- **CSS 선택자**: HTML 요소 선택자 (예: `div.price`, `#content > span`)
- **HTML 속성**: 추출할 속성 (`text` 또는 속성명)
- **값 템플릿**: Jinja2 템플릿 (선택사항)

#### Text 응답
- **정규 표현식**: 텍스트 패턴 (예: `temperature: ([\d.]+)`)
- **정규식 그룹**: 캡처 그룹 번호
- **값 템플릿**: Jinja2 템플릿 (선택사항)

## 실제 사용 예시

### 예시 1: 날씨 API (JSON)
```yaml
이름: 서울 날씨
URL: https://api.openweathermap.org/data/2.5/weather
메소드: GET
응답 타입: json
URL 파라미터: {"q": "Seoul", "appid": "YOUR_API_KEY", "units": "metric"}
JSON 경로: main.temp
값 템플릿: {{ value | round(1) }}°C
```

### 예시 2: 웹페이지 가격 (HTML)
```yaml
이름: 제품 가격
URL: https://shopping.example.com/product/12345
메소드: GET
응답 타입: html
CSS 선택자: span.price-now
HTML 속성: text
값 템플릿: {{ value | replace(',', '') | replace('원', '') | int }}
```

### 예시 3: 서버 상태 (Text)
```yaml
이름: 서버 CPU
URL: https://status.example.com/metrics.txt
메소드: GET
응답 타입: text
정규 표현식: CPU Usage: ([\d.]+)%
정규식 그룹: 1
값 템플릿: {{ value | float }}
```

### 예시 4: API 인증 (POST)
```yaml
이름: API 데이터
URL: https://api.example.com/query
메소드: POST
응답 타입: json
헤더: {"Content-Type": "application/json", "X-API-Key": "SECRET"}
요청 본문: {"action": "get_status", "format": "json"}
JSON 경로: result.status
```

## 템플릿 변수

값 템플릿에서 사용 가능한 변수:
- `value`: 파싱된 값
- `response`: 전체 응답 텍스트
- `json`: JSON 응답 (json 타입인 경우)
- `status`: HTTP 상태 코드

### 템플릿 예시
```jinja2
# 숫자 반올림
{{ value | round(2) }}

# 텍스트 변환
{% if value == "OK" %}정상{% else %}오류{% endif %}

# 단위 추가
{{ value }} kWh

# 계산
{{ (value | float) * 1.1 | round(2) }}
```

## 센서 속성

생성된 센서는 다음 속성을 제공합니다:
- `http_status`: HTTP 응답 코드
- `response_type`: 응답 타입 (json/html/text)
- `url`: 요청 URL
- `method`: HTTP 메소드
- `json_response`: JSON 전체 응답 (json 타입인 경우)

## 문제 해결

### 센서가 "unavailable" 상태
1. URL이 올바른지 확인
2. 네트워크 연결 확인
3. SSL 오류시 SSL 검증 비활성화
4. 타임아웃 값 증가
5. 개발자 도구 → 로그에서 오류 확인

### 파싱 오류
1. 응답 형식 확인 (개발자 도구 사용)
2. JSON 경로/CSS 선택자/정규식 문법 확인
3. 센서의 `json_response` 속성에서 실제 응답 확인

## 보안 권장사항

API 키와 토큰은 `secrets.yaml`에 저장:
```yaml
# secrets.yaml
weather_api_key: "your-api-key"

# 통합 설정에서
URL 파라미터: {"appid": "!secret weather_api_key"}
```

## 라이선스

MIT License

## 제작자

**Pages in Korea (pages.kr)**
- 웹사이트: [https://pages.kr](https://pages.kr)
- GitHub: [@pageskr](https://github.com/pageskr)