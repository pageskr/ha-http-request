# HTTP Request - Home Assistant 커스텀 통합

[![GitHub](https://img.shields.io/github/license/pageskr/ha-http-request)](https://github.com/pageskr/ha-http-request/blob/main/LICENSE)
[![GitHub release](https://img.shields.io/github/release/pageskr/ha-http-request.svg)](https://github.com/pageskr/ha-http-request/releases)

HTTP Request 통합은 HTTP 요청을 통해 외부 API나 웹 페이지에서 데이터를 가져와 Home Assistant 센서로 만들어주는 기능을 제공합니다.

제작: **Pages in Korea (pages.kr)**  
GitHub: [https://github.com/pageskr/ha-http-request](https://github.com/pageskr/ha-http-request)

## 주요 기능

- 🌐 **다양한 HTTP 메소드 지원**: GET, POST, PUT, PATCH, DELETE
- 📊 **세 가지 응답 형식 파싱**:
  - **JSON**: JMESPath를 사용한 데이터 추출
  - **HTML**: CSS Selector를 사용한 요소 선택
  - **Text**: 정규식을 사용한 패턴 매칭
- 🎯 **Jinja2 템플릿 지원**: 센서 값과 속성을 동적으로 변환
- 🔧 **유연한 설정**: 헤더, 파라미터, 본문, 타임아웃, SSL 옵션
- 🏠 **Home Assistant 기기 통합**: 센서들이 하나의 기기로 그룹화
- 🌍 **다국어 지원**: 한국어, 영어

## 설치 방법

### HACS를 통한 설치 (권장)
1. HACS → 통합 → 우측 상단 메뉴 → 사용자 정의 저장소
2. 저장소 URL: `https://github.com/pageskr/ha-http-request`
3. 카테고리: `통합` 선택
4. 저장 후 HACS에서 "HTTP Request" 검색하여 설치
5. Home Assistant 재시작

### 수동 설치
1. [최신 릴리즈](https://github.com/pageskr/ha-http-request/releases)에서 `ha-http-request.zip` 다운로드
2. Home Assistant의 `custom_components` 디렉토리에 압축 해제
3. Home Assistant 재시작

## 사용 방법

### 통합 추가
1. **설정** → **기기 및 서비스** → **통합 추가**
2. "HTTP Request" 검색
3. 설정 입력 후 저장

### 설정 항목 설명

#### 기본 설정
| 항목 | 설명 | 필수 | 기본값 |
|------|------|:----:|--------|
| **이름** | 센서 이름 | ✅ | HTTP Request Sensor |
| **메소드** | HTTP 메소드 | ✅ | GET |
| **URL** | 데이터를 가져올 URL | ✅ | - |
| **헤더** | HTTP 헤더 (JSON) | ❌ | {} |
| **파라미터** | URL 파라미터 (JSON) | ❌ | {} |
| **본문** | 요청 본문 (JSON) | ❌ | {} |
| **타임아웃** | 응답 대기 시간(초) | ❌ | 15 |
| **SSL 검증** | SSL 인증서 검증 | ❌ | true |
| **업데이트 간격** | 데이터 갱신 주기(초) | ❌ | 60 |

#### 응답 파싱 설정
| 항목 | 설명 | 응답 타입 |
|------|------|-----------|
| **응답 타입** | json, html, text 중 선택 | 모두 |
| **JMESPath** | JSON 데이터 추출 경로 | json |
| **CSS 선택자** | HTML 요소 선택자 | html |
| **HTML 속성** | 추출할 속성 | html |
| **정규식** | 텍스트 추출 패턴 | text |
| **정규식 그룹** | 캡처 그룹 번호 | text |

#### 템플릿 설정
| 항목 | 설명 |
|------|------|
| **값 템플릿** | Jinja2 템플릿으로 센서 값 변환 |

### 템플릿 변수
템플릿에서 사용 가능한 변수:
- `value`: 파싱된 원본 값
- `json`: JSON 응답 전체 (json 타입인 경우)
- `text`: 텍스트 응답 전체
- `status`: HTTP 상태 코드

## 실제 사용 예시

### 예시 1: OpenWeatherMap API
```yaml
이름: 서울 날씨
URL: https://api.openweathermap.org/data/2.5/weather?q=Seoul&appid=YOUR_API_KEY
응답 타입: json
JMESPath: main.temp
값 템플릿: {{ (value - 273.15) | round(1) }}°C
```

### 예시 2: 웹페이지 가격 모니터링
```yaml
이름: 제품 가격
URL: https://shopping.example.com/product/12345
응답 타입: html
CSS 선택자: span.price-now
HTML 속성: text
값 템플릿: {{ value | replace(',', '') | replace('원', '') | int }}
```

### 예시 3: 서버 상태 체크
```yaml
이름: 서버 상태
URL: https://status.example.com/health
응답 타입: text
정규식: status:\s*(\w+)
정규식 그룹: 1
값 템플릿: {% if value == "OK" %}정상{% else %}오류{% endif %}
```

### 예시 4: 추가 속성 설정 (JSON)
```json
[
  {
    "key": "humidity",
    "response_type": "json",
    "json_jmes": "main.humidity",
    "attr_template": "{{ value }}%"
  },
  {
    "key": "wind_speed",
    "response_type": "json",
    "json_jmes": "wind.speed",
    "attr_template": "{{ (value * 3.6) | round(1) }} km/h"
  }
]
```

## 고급 기능

### POST 요청 예시
```yaml
메소드: POST
헤더: {"Content-Type": "application/json", "Authorization": "Bearer YOUR_TOKEN"}
본문: {"query": "temperature", "location": "Seoul"}
```

### 복잡한 JMESPath 예시
```yaml
# 배열의 첫 번째 요소
JMESPath: results[0].value

# 조건부 선택
JMESPath: items[?status=='active'].name | [0]

# 중첩된 데이터
JMESPath: data.sensors.temperature.current
```

### CSS Selector 예시
```yaml
# 클래스로 선택
CSS 선택자: .price-tag

# ID로 선택
CSS 선택자: #main-content

# 복잡한 선택자
CSS 선택자: div.container > ul > li:nth-child(2) > span.value
```

## 문제 해결

### "Unavailable" 상태
1. **URL 확인**: 브라우저에서 URL이 작동하는지 확인
2. **네트워크**: Home Assistant가 해당 URL에 접근 가능한지 확인
3. **SSL 오류**: 자체 서명 인증서의 경우 SSL 검증을 비활성화
4. **타임아웃**: 응답이 느린 경우 타임아웃 값 증가
5. **로그 확인**: 설정 → 시스템 → 로그에서 오류 확인

### 파싱 오류
1. **응답 확인**: 개발자 도구나 Postman으로 실제 응답 확인
2. **문법 검증**:
   - JMESPath: [JMESPath.org](https://jmespath.org/)에서 테스트
   - CSS: 브라우저 개발자 도구에서 확인
   - 정규식: [regex101.com](https://regex101.com/)에서 테스트
3. **인코딩**: UTF-8이 아닌 경우 문제 발생 가능

## 보안 권장사항

### API 키 보호
```yaml
# secrets.yaml
weather_api_key: "your-actual-api-key-here"
github_token: "ghp_xxxxxxxxxxxx"

# 통합 설정에서
URL: https://api.openweathermap.org/data/2.5/weather?appid=!secret weather_api_key
헤더: {"Authorization": "Bearer !secret github_token"}
```

### SSL 인증서
- 가능한 SSL 검증을 활성화 상태로 유지
- 자체 서명 인증서는 Home Assistant의 신뢰 저장소에 추가

## 기여하기

1. 이 저장소를 포크하세요
2. 새로운 기능 브랜치를 만드세요 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋하세요 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시하세요 (`git push origin feature/amazing-feature`)
5. Pull Request를 열어주세요

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](https://github.com/pageskr/ha-http-request/blob/main/LICENSE) 파일을 참조하세요.

## 제작자

**Pages in Korea (pages.kr)**
- 웹사이트: [https://pages.kr](https://pages.kr)
- 이메일: support@pages.kr
- GitHub: [@pageskr](https://github.com/pageskr)

---

문제가 있거나 기능 제안이 있으시면 [이슈](https://github.com/pageskr/ha-http-request/issues)를 열어주세요!