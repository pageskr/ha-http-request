# Home Assistant HTTP Request Integration

HTTP Request를 통해 데이터를 가져와 센서로 만들어주는 Home Assistant 커스텀 통합입니다.

## 주요 기능

- **다양한 HTTP 메소드 지원**: GET, POST, PUT, DELETE, PATCH
- **유연한 응답 파싱**: JSON, HTML, Text 형식 지원
- **고급 템플릿 에디터**: 코드 에디터를 통한 편리한 Jinja2 템플릿 작성
- **다중 센서**: 하나의 HTTP 요청으로 여러 센서 생성 가능
- **기존값 유지**: 오류 발생 시 센서의 기존 상태값 유지 옵션
- **설정 초기화**: 템플릿 설정을 쉽게 초기화할 수 있는 옵션
- **실시간 업데이트**: 설정 가능한 주기로 자동 데이터 갱신

## 설치 방법

### HACS를 통한 설치 (권장)
1. HACS에서 "통합" 탭을 선택합니다
2. 우측 상단의 점 3개 메뉴를 클릭하고 "사용자 지정 저장소"를 선택합니다
3. 저장소 URL에 `https://github.com/pageskr/ha-http-request`를 입력하고 카테고리는 "통합"을 선택합니다
4. "추가" 버튼을 클릭합니다
5. HACS에서 "HTTP Request"를 검색하여 설치합니다
6. Home Assistant를 재시작합니다

### 수동 설치
1. [최신 릴리즈](https://github.com/pageskr/ha-http-request/releases)에서 소스 코드를 다운로드합니다
2. `custom_components/http_request` 폴더를 Home Assistant의 `custom_components` 디렉토리에 복사합니다
3. Home Assistant를 재시작합니다

## 설정 방법

### 1. 통합 추가
1. Home Assistant 설정 → 기기 및 서비스 → 통합 추가
2. "HTTP Request" 검색 및 선택
3. 서비스 이름 입력 (예: "날씨 API", "스마트 미터" 등)

### 2. HTTP 요청 설정
- **URL**: 요청할 URL 주소
- **SSL 인증서 검증**: SSL 인증서 검증 여부 (자체 서명 인증서 사용 시 비활성화)
- **HTTP 메소드**: GET, POST, PUT, DELETE, PATCH 중 선택
- **요청 헤더**: JSON 형식의 헤더 (코드 에디터 제공)
  ```json
  {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
  }
  ```
- **요청 변수**: URL 파라미터 또는 폼 데이터 (JSON 형식)
  ```json
  {
    "api_key": "YOUR_API_KEY",
    "format": "json"
  }
  ```
- **요청 본문**: POST, PUT, PATCH 메소드에서 사용하는 본문 데이터
- **타임아웃**: 요청 타임아웃 시간 (1-300초)
- **업데이트 간격**: 데이터 갱신 주기 (30-86400초)
- **응답 타입**: JSON, HTML, Text 중 선택

### 3. 센서 추가

#### JSON 센서
JSON 응답에서 특정 값을 추출하여 센서로 만듭니다.

- **JSON 경로**: 점 표기법으로 값 추출
  - 단순 경로: `temperature`, `data.current.temp`
  - 배열 접근: `items[0].name`, `results[2].value`
  - 복잡한 경로: `data.sensors[0].readings.temperature`
- **값 템플릿**: Jinja2 템플릿으로 값 변환 (코드 에디터)
- **속성 템플릿**: JSON 형식으로 추가 속성 정의 (코드 에디터)
- **단위**: 센서 값의 단위 (°C, %, kWh 등)
- **기존값 유지**: 오류 시 이전 상태값 유지

#### HTML 센서
웹 페이지에서 특정 요소의 값을 추출하여 센서로 만듭니다.

- **CSS 선택자**: HTML 요소 선택
  - ID 선택: `#temperature`
  - 클래스 선택: `.current-temp`
  - 복잡한 선택: `div.weather-widget > span.temp`
- **HTML 값 유형**:
  - `텍스트 값`: 요소의 텍스트 내용만 추출
  - `속성 값`: 요소의 특정 속성값 추출 (href, src, data-* 등)
  - `HTML 내용`: 요소의 내부 HTML (innerHTML)
  - `outerHTML 내용`: 요소 자체를 포함한 전체 HTML
- **HTML 속성 이름**: "속성 값" 선택 시 추출할 속성명
- **값 템플릿**: Jinja2 템플릿으로 값 변환 (코드 에디터)
- **속성 템플릿**: JSON 형식으로 추가 속성 정의 (코드 에디터)
- **단위**: 센서 값의 단위
- **기존값 유지**: 오류 시 이전 상태값 유지

#### Text 센서
텍스트 응답에서 정규 표현식으로 값을 추출하여 센서로 만듭니다.

- **정규 표현식**: 텍스트에서 값 추출
  - 숫자 추출: `Temperature: (\d+\.?\d*)`
  - 여러 값 추출: `(\w+): (\d+)`
- **정규식 그룹 개수**: 속성에 저장할 매치 개수 (1-50)
- **값 템플릿**: Jinja2 템플릿으로 값 변환 (코드 에디터)
- **속성 템플릿**: JSON 형식으로 추가 속성 정의 (코드 에디터)
- **단위**: 센서 값의 단위
- **기존값 유지**: 오류 시 이전 상태값 유지

### 4. 센서 수정
- 기존 센서의 설정을 변경할 수 있습니다
- **설정 초기화**: 체크 시 값 템플릿, 속성 템플릿, 단위 설정이 모두 초기화됩니다
  - HTML 센서의 경우 HTML 속성 이름도 함께 초기화됩니다

## 템플릿 변수

값 템플릿과 속성 템플릿에서 사용 가능한 변수:

### 공통 변수
- `response`: 원본 응답 텍스트
- `status`: HTTP 상태 코드

### JSON 센서 변수
- `json`: 전체 JSON 응답 객체
- `value`: JSON 경로로 추출된 값

### HTML 센서 변수
- `html`: 전체 HTML 응답 텍스트
- `value`: CSS 선택자와 값 유형에 따라 추출된 값

### Text 센서 변수
- `text`: 전체 텍스트 응답
- `value`: 
  - 정규식 사용 시: 모든 매치 결과의 배열
  - 정규식 미사용 시: 전체 텍스트

## 템플릿 예제

### 값 템플릿 예제

#### 기본 변환
```jinja2
# 숫자 반올림
{{ value | round(2) }}

# 단위 변환 (섭씨 → 화씨)
{{ (value * 9/5 + 32) | round(1) }}

# 조건부 값
{% if value > 100 %}높음{% elif value > 50 %}보통{% else %}낮음{% endif %}

# 텍스트 변환
{{ value | upper }}
{{ value | replace("ON", "켜짐") | replace("OFF", "꺼짐") }}
```

#### JSON 센서 고급 예제
```jinja2
# 복잡한 조건 처리
{% if json.status == "ok" and json.data %}
  {{ json.data.temperature | round(1) }}
{% else %}
  unavailable
{% endif %}

# 여러 값 조합
{{ json.temperature }}°C / {{ json.humidity }}%

# 배열 처리
{% set temps = json.sensors | map(attribute='temperature') | list %}
평균: {{ temps | average | round(1) }}°C
```

#### HTML 센서 예제
```jinja2
# 단위 제거 및 숫자 변환
{{ value | regex_replace('[^0-9.]', '') | float }}

# HTML 태그 제거 (outerHTML 사용 시)
{{ value | regex_replace('<[^>]+>', '') | trim }}
```

#### Text 센서 배열 처리
```jinja2
# 첫 번째 매치만 사용
{{ value[0] if value else "N/A" }}

# 모든 매치를 쉼표로 연결
{{ value | join(", ") }}

# 매치 개수
총 {{ value | length }}개 발견

# 특정 인덱스 접근 (안전하게)
{{ value[2] if value | length > 2 else "없음" }}
```

### 속성 템플릿 예제

#### 기본 속성
```json
{
  "raw_value": "{{ value }}",
  "last_updated": "{{ now().strftime('%Y-%m-%d %H:%M:%S') }}",
  "status": "{% if status == 200 %}정상{% else %}오류 ({{ status }}){% endif %}"
}
```

#### JSON 센서 고급 속성
```json
{
  "all_sensors": "{{ json.sensors | length if json.sensors else 0 }}",
  "sensor_names": "{{ json.sensors | map(attribute='name') | list | join(', ') if json.sensors else '' }}",
  "min_temp": "{{ json.sensors | map(attribute='temperature') | min if json.sensors else 0 }}",
  "max_temp": "{{ json.sensors | map(attribute='temperature') | max if json.sensors else 0 }}",
  "data_quality": "{% if json.quality > 0.9 %}우수{% elif json.quality > 0.7 %}양호{% else %}불량{% endif %}"
}
```

#### Text 센서 매치 정보
```json
{
  "match_count": "{{ value | length if value else 0 }}",
  "all_matches": "{{ value | join(', ') if value else '매치 없음' }}",
  "first_match": "{{ value[0] if value else 'N/A' }}",
  "last_match": "{{ value[-1] if value else 'N/A' }}"
}
```

## 기존값 유지 기능

"기존값 유지" 옵션을 활성화하면 다음과 같은 경우에 센서의 이전 상태값이 유지됩니다:

- 값 템플릿 결과가 `false`, `none`, `unknown`, `unavailable`인 경우
- Jinja2 템플릿 처리 중 오류가 발생한 경우
- HTTP 요청이 실패한 경우 (네트워크 오류, 타임아웃 등)

이 기능은 다음과 같은 상황에서 유용합니다:
- 일시적인 네트워크 문제
- API 서버의 일시적 장애
- 템플릿 처리 중 예상치 못한 데이터 형식

**주의**: "기존값 유지"는 센서의 마지막 유효한 상태값을 유지하는 것이지, 현재 HTTP 응답의 원본 값을 유지하는 것이 아닙니다.

## 센서 속성

### 기본 속성
모든 센서는 다음 기본 속성을 포함합니다:
- `sensor_index`: 센서 인덱스 (생성 순서)
- `sensor_name`: 센서 이름
- `sensor_update`: 마지막 업데이트 시간
- `unit_of_measurement`: 설정된 단위 (있는 경우)

### 센서 타입별 추가 속성

#### JSON 센서
- `json_path`: 사용된 JSON 경로

#### HTML 센서
- `html_selector`: 사용된 CSS 선택자
- `html_value_type`: 선택된 값 유형 (value/attribute/html/outerhtml)
- `html_attr_name`: 속성 이름 (속성 유형인 경우)

#### Text 센서
- `text_regex`: 사용된 정규 표현식
- `text_group_count`: 설정된 그룹 개수
- `text_matches`: 매치된 결과 (그룹 개수만큼만 표시)
- `text_total_count`: 전체 매치 개수 (실제 발견된 모든 매치)

## 실제 사용 예제

### 날씨 API (JSON)
```yaml
URL: https://api.openweathermap.org/data/2.5/weather?q=Seoul&appid=YOUR_API_KEY
응답 타입: JSON
JSON 경로: main.temp
값 템플릿: {{ (value - 273.15) | round(1) }}
단위: °C
```

### 전력 사용량 웹페이지 (HTML)
```yaml
URL: http://192.168.1.100/power
응답 타입: HTML
CSS 선택자: span.power-usage
HTML 값 유형: 텍스트 값
값 템플릿: {{ value | regex_replace('[^0-9.]', '') | float }}
단위: kW
```

### 로그 파일 모니터링 (Text)
```yaml
URL: http://192.168.1.50/logs/latest.txt
응답 타입: Text
정규 표현식: ERROR: (.+)
정규식 그룹 개수: 10
값 템플릿: {{ value | length }} errors found
```

## 문제 해결

### 센서가 업데이트되지 않음
1. URL과 네트워크 연결 확인
2. SSL 인증서 문제인 경우 "SSL 인증서 검증" 비활성화
3. Home Assistant 로그에서 오류 메시지 확인
4. 개발자 도구 → 상태에서 센서 상태 및 속성 확인

### 값이 올바르게 파싱되지 않음
1. 응답 타입이 실제 응답과 일치하는지 확인
2. JSON 경로, CSS 선택자, 정규 표현식이 올바른지 확인
3. 브라우저 개발자 도구나 API 테스트 도구로 실제 응답 확인
4. 템플릿 테스터에서 변수와 템플릿 테스트

### 템플릿 오류
1. Home Assistant 개발자 도구 → 템플릿에서 테스트
2. 변수명 확인 (`value`, `json`, `html`, `text`, `response`, `status`)
3. Jinja2 문법 확인 (괄호, 따옴표 등)
4. 속성 템플릿은 유효한 JSON 형식이어야 함 (JSON 검증 도구 사용)

### 흔한 실수
- JSON 경로에서 대소문자 구분
- HTML 선택자에서 특수문자 이스케이프
- 정규 표현식에서 그룹 괄호 `()` 누락
- 템플릿에서 `None` 값 처리 누락

## 고급 팁

1. **여러 값을 하나의 센서로**: 속성 템플릿을 활용하여 여러 값을 하나의 센서에 저장
2. **조건부 업데이트**: 값 템플릿에서 조건을 검사하여 특정 조건에서만 업데이트
3. **데이터 변환**: 템플릿을 사용하여 텍스트를 숫자로, 시간 형식 변환 등
4. **오류 처리**: `default` 필터를 사용하여 기본값 설정

## 기여하기

이 프로젝트에 기여하고 싶으시다면:
1. 이슈를 생성하여 버그를 보고하거나 기능을 제안해주세요
2. Pull Request를 통해 코드 개선에 참여해주세요
3. 문서 개선이나 번역에 도움을 주세요

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 문의 및 지원

- GitHub Issues: https://github.com/pageskr/ha-http-request/issues
- 제작자: pages.kr
