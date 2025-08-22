# Home Assistant HTTP Request Integration

HTTP Request를 통해 데이터를 가져와 센서로 만들어주는 Home Assistant 커스텀 통합입니다.

## 주요 기능

- **다양한 HTTP 메소드 지원**: GET, POST, PUT, DELETE, PATCH
- **유연한 응답 파싱**: JSON, HTML, Text 형식 지원
- **템플릿 지원**: Jinja2 템플릿을 사용한 값 변환 및 속성 추가
- **다중 센서**: 하나의 HTTP 요청으로 여러 센서 생성 가능
- **기존값 유지**: 오류 발생 시 센서의 기존 상태값 유지 옵션
- **설정 초기화**: 템플릿 설정을 쉽게 초기화할 수 있는 옵션

## 설치 방법

### HACS를 통한 설치 (권장)
1. HACS에서 "통합" 탭을 선택합니다
2. 우측 상단의 점 3개 메뉴를 클릭하고 "사용자 지정 저장소"를 선택합니다
3. 저장소 URL에 `https://github.com/YOUR_USERNAME/ha-http-request`를 입력하고 카테고리는 "통합"을 선택합니다
4. "추가" 버튼을 클릭합니다
5. HACS에서 "HTTP Request"를 검색하여 설치합니다
6. Home Assistant를 재시작합니다

### 수동 설치
1. `custom_components/http_request` 폴더를 Home Assistant의 `custom_components` 디렉토리에 복사합니다
2. Home Assistant를 재시작합니다

## 설정 방법

### 1. 통합 추가
1. Home Assistant 설정 → 기기 및 서비스 → 통합 추가
2. "HTTP Request" 검색 및 선택
3. 서비스 이름 입력

### 2. HTTP 요청 설정
- **URL**: 요청할 URL 주소
- **SSL 인증서 검증**: SSL 인증서 검증 여부
- **HTTP 메소드**: GET, POST, PUT, DELETE, PATCH 중 선택
- **요청 헤더**: JSON 형식 (예: `{"Authorization": "Bearer token"}`)
- **요청 변수**: JSON 형식 (예: `{"param1": "value1"}`)
- **요청 본문**: JSON 형식 (POST, PUT, PATCH 메소드에서 사용)
- **타임아웃**: 요청 타임아웃 시간 (1-300초)
- **업데이트 간격**: 데이터 갱신 주기 (30-86400초)
- **응답 타입**: JSON, HTML, Text 중 선택

### 3. 센서 추가

#### JSON 센서
- **JSON 경로**: 점 표기법으로 값 추출 (예: `data.temperature`, `items[0].value`)
- **값 템플릿**: Jinja2 템플릿으로 값 변환
- **속성 템플릿**: JSON 형식으로 추가 속성 정의
- **단위**: 센서 값의 단위
- **기존값 유지**: 오류 시 이전 상태값 유지

#### HTML 센서
- **CSS 선택자**: HTML 요소 선택
- **HTML 값 유형**:
  - `텍스트 값`: 요소의 텍스트 내용
  - `속성 값`: 요소의 특정 속성값
  - `HTML 내용`: 요소의 내부 HTML
  - `outerHTML 내용`: 요소 자체를 포함한 전체 HTML
- **HTML 속성 이름**: 속성 값 선택 시 사용
- **값 템플릿**: Jinja2 템플릿으로 값 변환
- **속성 템플릿**: JSON 형식으로 추가 속성 정의
- **단위**: 센서 값의 단위
- **기존값 유지**: 오류 시 이전 상태값 유지

#### Text 센서
- **정규 표현식**: 텍스트에서 값 추출
- **정규식 그룹 개수**: 속성에 저장할 매치 개수 (1-50)
- **값 템플릿**: Jinja2 템플릿으로 값 변환
- **속성 템플릿**: JSON 형식으로 추가 속성 정의
- **단위**: 센서 값의 단위
- **기존값 유지**: 오류 시 이전 상태값 유지

### 4. 센서 수정
- 기존 센서의 설정을 변경할 수 있습니다
- **설정 초기화**: 체크 시 값 템플릿, 속성 템플릿, 단위 설정이 초기화됩니다

## 템플릿 변수

값 템플릿과 속성 템플릿에서 사용 가능한 변수:

### 공통 변수
- `response`: 원본 응답 텍스트
- `status`: HTTP 상태 코드

### JSON 센서
- `json`: 전체 JSON 응답 데이터
- `value`: JSON 경로로 추출된 값

### HTML 센서
- `html`: 전체 HTML 응답
- `value`: CSS 선택자와 값 유형에 따라 추출된 값

### Text 센서
- `text`: 전체 텍스트 응답
- `value`: 
  - 정규식 사용 시: 모든 매치 결과의 배열
  - 정규식 미사용 시: 전체 텍스트

## 템플릿 예제

### 값 템플릿 예제

```jinja2
# 숫자 반올림
{{ value | round(2) }}

# 조건부 값
{% if value > 100 %}높음{% else %}정상{% endif %}

# 텍스트 변환
{{ value | upper }}

# JSON 센서에서 복잡한 처리
{% if json.status == "ok" %}{{ json.data.temperature }}{% else %}오류{% endif %}

# Text 센서에서 배열 처리 (정규식 사용 시)
{{ value[0] if value else "매치 없음" }}
{{ value | join(", ") }}
```

### 속성 템플릿 예제

```json
{
  "raw_value": "{{ value }}",
  "timestamp": "{{ now() }}",
  "status": "{% if status == 200 %}정상{% else %}오류{% endif %}",
  "count": "{{ value | length if value is iterable else 0 }}"
}
```

## 기존값 유지 기능

"기존값 유지" 옵션을 활성화하면:
- 값 템플릿 결과가 `false`, `none`, `unknown`, `unavailable`인 경우
- Jinja2 템플릿 오류가 발생한 경우
- 센서의 이전 상태값이 그대로 유지됩니다

이 기능은 일시적인 오류나 네트워크 문제로 인해 센서 값이 손실되는 것을 방지합니다.

## 센서 속성

모든 센서는 다음 기본 속성을 포함합니다:
- `sensor_index`: 센서 인덱스
- `sensor_name`: 센서 이름
- `sensor_update`: 마지막 업데이트 시간

### 추가 속성

#### JSON 센서
- `json_path`: 사용된 JSON 경로

#### HTML 센서
- `html_selector`: 사용된 CSS 선택자
- `html_value_type`: 선택된 값 유형
- `html_attr_name`: 속성 이름 (속성 유형인 경우)

#### Text 센서
- `text_regex`: 사용된 정규 표현식
- `text_group_count`: 설정된 그룹 개수
- `text_matches`: 매치된 결과 (그룹 개수만큼)
- `text_total_count`: 전체 매치 개수

## 문제 해결

### 센서가 업데이트되지 않음
- URL과 네트워크 연결 확인
- SSL 인증서 문제인 경우 "SSL 인증서 검증" 비활성화
- Home Assistant 로그에서 오류 메시지 확인

### 값이 올바르게 파싱되지 않음
- JSON 경로, CSS 선택자, 정규 표현식이 올바른지 확인
- 개발자 도구의 템플릿 테스터에서 템플릿 테스트
- 응답 타입이 실제 응답과 일치하는지 확인

### 템플릿 오류
- Jinja2 문법 확인
- 변수명이 올바른지 확인 (`value`, `json`, `html`, `text`, `response`, `status`)
- 속성 템플릿은 유효한 JSON 형식이어야 함

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
