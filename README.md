# HTTP Request - Home Assistant 커스텀 통합

이 통합은 HTTP 요청을 통해 외부 API나 웹 페이지에서 데이터를 가져와 Home Assistant 센서로 만들어주는 기능을 제공합니다.

## 설치 방법

1. Home Assistant 설정 디렉토리의 `custom_components` 폴더에 `http_request` 폴더를 복사합니다.
   - 일반적인 경로: `/config/custom_components/http_request/`

2. Home Assistant를 재시작합니다.

3. 설정 → 통합 → "통합 추가" 버튼 클릭 → "HTTP Request" 검색 → 추가

## 사용 방법

### 센서 추가
1. HTTP Request 통합을 추가할 때마다 새로운 센서가 하나씩 생성됩니다.
2. 여러 개의 센서가 필요하면 통합을 여러 번 추가하세요.

### 주요 설정 옵션

#### 기본 설정
- **name**: 센서 이름
- **method**: HTTP 메소드 (GET, POST, PUT, PATCH, DELETE)
- **url**: 요청할 URL
- **headers**: HTTP 헤더 (JSON 형식)
- **params**: URL 파라미터 (JSON 형식)
- **body**: 요청 본문 (JSON 형식)
- **timeout**: 타임아웃 (초 단위, 기본값: 15)
- **verify_ssl**: SSL 인증서 검증 여부 (기본값: true)
- **scan_interval**: 갱신 주기 (초 단위, 기본값: 60, 최소: 10)

#### 응답 파싱 설정
- **response_type**: 응답 타입 선택 (json, html, text)

##### JSON 응답인 경우
- **json_jmes**: JMESPath 표현식
  - 예: `data.temperature`, `results[0].value`

##### HTML 응답인 경우
- **html_selector**: CSS 선택자
  - 예: `div.price`, `#content > span.value`
- **html_attr**: 추출할 속성 (기본값: "text")
  - `text`: 요소의 텍스트 내용
  - `href`, `src`, `data-*` 등: 특정 속성 값

##### 텍스트 응답인 경우
- **text_regex**: 정규식 패턴
  - 예: `temperature: ([\d.]+)`
- **text_group**: 캡처 그룹 번호 (기본값: 1)

#### 추가 속성 (Attributes)
센서의 추가 속성을 설정할 수 있습니다. 각 속성은 독립적으로 파싱 방식을 지정할 수 있습니다.

```json
[
  {
    "key": "humidity",
    "response_type": "json",
    "json_jmes": "data.humidity"
  },
  {
    "key": "last_update",
    "response_type": "html",
    "html_selector": "span.update-time",
    "html_attr": "text"
  }
]
```

## 실제 사용 예시

### 예시 1: 날씨 API (JSON)
- URL: `https://api.weather.com/current`
- Response Type: `json`
- JMESPath: `main.temp`
- Attributes:
  ```json
  [
    {"key": "humidity", "response_type": "json", "json_jmes": "main.humidity"},
    {"key": "pressure", "response_type": "json", "json_jmes": "main.pressure"}
  ]
  ```

### 예시 2: 웹 페이지 스크래핑 (HTML)
- URL: `https://example.com/product/123`
- Response Type: `html`
- HTML Selector: `span.price`
- HTML Attr: `text`
- Attributes:
  ```json
  [
    {"key": "stock", "response_type": "html", "html_selector": "div.stock-status", "html_attr": "text"},
    {"key": "image_url", "response_type": "html", "html_selector": "img.product", "html_attr": "src"}
  ]
  ```

### 예시 3: 텍스트 파일 파싱
- URL: `https://example.com/status.txt`
- Response Type: `text`
- Text Regex: `CPU: (\d+)%`
- Text Group: `1`
- Attributes:
  ```json
  [
    {"key": "memory", "response_type": "text", "text_regex": "Memory: (\\d+)%", "text_group": 1},
    {"key": "disk", "response_type": "text", "text_regex": "Disk: (\\d+)%", "text_group": 1}
  ]
  ```

## 문제 해결

### 센서가 "unavailable" 상태인 경우
1. URL이 올바른지 확인
2. 네트워크 연결 상태 확인
3. SSL 인증서 문제인 경우 `verify_ssl`을 false로 설정
4. 타임아웃 값을 늘려보기
5. 헤더나 인증 정보가 필요한지 확인

### 파싱 오류
1. JMESPath, CSS Selector, 정규식이 올바른지 확인
2. 응답 형식이 예상과 일치하는지 확인
3. `http_status` 속성을 통해 HTTP 응답 코드 확인

## 보안 주의사항

1. API 키나 토큰은 `secrets.yaml`에 저장하고 참조하세요
2. SSL 검증을 비활성화하는 것은 보안상 위험할 수 있습니다
3. 민감한 정보가 포함된 URL은 주의해서 다루세요
4. 너무 짧은 갱신 주기는 대상 서버에 부담을 줄 수 있습니다

## 라이선스

이 통합은 Home Assistant의 라이선스 정책을 따릅니다.