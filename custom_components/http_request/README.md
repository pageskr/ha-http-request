# HTTP Request (Home Assistant Custom Integration)

> 기기(Device) 없이, 통합 추가 시 **센서 1개**가 생성됩니다.  
> 응답 타입에 따라 JSON/HTML/Text를 파싱해 **기본 state**와 **여러 attributes**를 설정할 수 있습니다.

## 특징
- 각 엔트리(센서)에 개별 요청 설정: `method`, `url`, `headers`, `params`, `body`, `timeout`, `verify_ssl`, `scan_interval`
- 응답 타입:
  - `json`: **JMESPath**로 원하는 객체/값 추출
  - `html`: **CSS Selector**로 요소 선택 + `text` 또는 특정 속성(`href`, `data-*`) 추출
  - `text`: **정규식** + `group` 인덱스로 원하는 패턴 추출
- state + attributes(복수) 모두 동일한 방식으로 추출 가능
- Device를 만들지 않으며, Entry=Sensor의 1:1 구조

## 설치
1. `custom_components/http_request/` 디렉토리에 소스 복사
2. Home Assistant 재시작
3. 설정 → 통합 → 통합 추가(`HTTP Request`) → 센서 정의
4. 필요시 여러 번 추가하여 센서를 여러 개 생성

## 설정 항목(추가 화면)
- **name**: 센서 이름
- **method**: `GET|POST|PUT|PATCH|DELETE`
- **url**: 호출할 전체 URL
- **headers/params/body**: JSON 형태(필요 시 비워둠)
- **timeout**: 요청 타임아웃(초) (기본 15)
- **verify_ssl**: SSL 검증 (기본 true)
- **scan_interval**: 갱신 주기(초) (기본 60, 최소 10)
- **response_type**: `json|html|text`

### 파싱 옵션
- `json`:
  - `json_jmes`: JMESPath 표현식 (예: `data.items[0].value`)
- `html`:
  - `html_selector`: CSS 선택자 (예: `div.price > span.value`)
  - `html_attr`: `text` 또는 속성명 (예: `href`)
- `text`:
  - `text_regex`: 정규식 (예: `price:\\s*(\\d+)`)
  - `text_group`: 캡처 그룹 인덱스 (기본 1)

### Attributes
`attributes`는 리스트입니다. 각 항목은 다음 키를 포함합니다.

```yaml
attributes:
  - key: "price"
    response_type: "html"
    html_selector: "span#nowPrice"
    html_attr: "text"
  - key: "version"
    response_type: "json"
    json_jmes: "meta.version"
  - key: "matched"
    response_type: "text"
    text_regex: "OK\\s+(\\w+)"
    text_group: 1
```

## 예시 1: JSON API

* `response_type=json`, `json_jmes=data.status`
* attributes:

  * `count`: `json_jmes=data.count`
  * `p95`: `json_jmes=metrics.latency.p95`

생성된 센서:

* `state` = `data.status`
* `attributes.count` = 정수
* `attributes.p95` = 밀리초

## 예시 2: HTML 페이지

* `response_type=html`, `html_selector="div.price > span.value"`, `html_attr="text"`
* attributes:

  * `currency`: selector `"div.price > span.cur"`, attr `"text"`
  * `link`: selector `"a.buy"`, attr `"href"`

## 예시 3: 텍스트 응답

* `response_type=text`, `text_regex="total:(\\d+)"`, `text_group=1`
* attributes:

  * `ok`: regex `"ok:(\\d+)"`, group `1`
  * `fail`: regex `"fail:(\\d+)"`, group `1`

## 로깅/트러블슈팅

* 센서가 `unavailable`이면 네트워크/인증/SSL 옵션, 정규식/JMESPath/Selector 오류 확인
* `http_status` attribute로 원격 응답 코드를 확인
* HTML 파싱 실패 시 selector를 간단히 줄여가며 테스트

## 보안 가이드

* 민감한 헤더/토큰은 `secrets.yaml`에 보관하고 UI 입력 시 최소 권한 토큰 사용
* 내부망/프록시를 통해 대상 화이트리스트 운용
* `verify_ssl=true` 유지, 내부 CA는 컨테이너/호스트에 신뢰 저장소 등록
* 정규식/셀렉터/JMESPath는 신뢰된 응답 구조에 맞게 제한적으로 사용(의도치 않은 데이터 노출 방지)