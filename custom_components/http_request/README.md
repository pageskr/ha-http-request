# HTTP Request (Home Assistant Custom Integration)

> HTTP 요청을 통해 외부 데이터를 가져와 센서로 만드는 Home Assistant 커스텀 통합

제작: **Pages in Korea (pages.kr)**  
GitHub: [https://github.com/pageskr/ha-http-request](https://github.com/pageskr/ha-http-request)

## 특징

- **다양한 HTTP 메소드 지원**: GET, POST, PUT, PATCH, DELETE
- **세 가지 응답 타입 파싱**:
  - `json`: JMESPath로 JSON 데이터 추출
  - `html`: CSS Selector로 HTML 요소 선택
  - `text`: 정규식으로 텍스트 패턴 매칭
- **Jinja2 템플릿 지원**: 센서 값과 속성을 동적으로 변환
- **기기 정보 제공**: "HTTP Request" 기기로 센서들을 그룹화
- **유연한 설정**: 헤더, 파라미터, 본문, 타임아웃, SSL 등

## 기술 사양

### 의존성
- `jmespath==1.0.1`: JSON 데이터 쿼리
- `beautifulsoup4==4.12.3`: HTML 파싱
- `lxml==4.9.3`: 고성능 XML/HTML 파서

### 파일 구조
```
http_request/
├── __init__.py          # 통합 초기화
├── manifest.json        # 통합 메타데이터
├── const.py            # 상수 정의
├── config_flow.py      # 설정 UI 플로우
├── sensor.py           # 센서 엔티티 구현
├── parser.py           # 파싱 및 템플릿 처리
├── strings.json        # UI 문자열
└── translations/       # 다국어 지원
    ├── en.json
    └── ko.json
```

## 구현 세부사항

### 데이터 업데이트 플로우
1. `DataUpdateCoordinator`가 설정된 주기로 HTTP 요청 실행
2. 응답을 설정된 타입(json/html/text)에 따라 파싱
3. 값 템플릿이 있으면 Jinja2로 변환
4. 센서 상태 및 속성 업데이트

### 템플릿 변수
```python
{
    "value": 파싱된_원본값,
    "json": JSON_응답_전체,  # json 타입인 경우
    "text": 텍스트_응답_전체,
    "status": HTTP_상태_코드
}
```

### 에러 처리
- 네트워크 오류: `UpdateFailed` 예외 발생
- 파싱 오류: None 반환 및 로그 기록
- JSON 파싱 실패: 빈 딕셔너리 반환

## 보안 고려사항

1. **SSL 검증**: 기본적으로 활성화
2. **타임아웃**: 무한 대기 방지
3. **민감 정보**: secrets.yaml 사용 권장
4. **입력 검증**: JSON 문자열 파싱시 안전 처리

## 확장 가능성

- OAuth2 인증 지원
- 응답 캐싱
- 재시도 로직
- GraphQL 지원
- WebSocket 연결

## 라이선스

MIT License - [LICENSE](https://github.com/pageskr/ha-http-request/blob/main/LICENSE) 참조

---

© 2024 Pages in Korea (pages.kr). All rights reserved.