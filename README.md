# AI 본부 관제 허브

재민 사장과 맥미니 본부장이 함께 쓰는 모바일 관제 화면입니다. 2026-11-18에 **1실 6그룹** 체제로 개편하고, 같은 날 애슬레틱·자기개발그룹의 실제 계획(수영 강습·헬스 독학·영어 유튜브 팟캐스트·자격증)을 반영했습니다.

- `index.html` — 화면 (4탭: 조직도 · 작업 보드 · 리셀·프로모션 · 시스템)
- `data.json` — 화면에 들어가는 상태 데이터 (조직도 · 알림 · KPI · 보드 · 응모 · 자동화 현황)
- `hub.html` — 데이터를 안에 넣은 단독 실행용 파일 (`index.html` + `data.json`)
- `build.py` — `data.json`을 `index.html`에 넣어 `hub.html`을 다시 만듭니다 (`python3 build.py`)
- `render_check.py` — 브라우저 없이 렌더링을 점검합니다 (`python3 render_check.py hub.html --brief`)
- `manifest.webmanifest`, `icon-*.png` — 홈 화면에 앱처럼 추가하기 위한 파일

색인을 막아 두었습니다(`noindex`). 전화번호·이메일·상세 주소·카드/주문 정보·직장(회사·사업장) 이름은 넣지 않습니다.
데이터를 바꾸려면 `data.json`만 고치고 `python3 build.py`를 다시 실행하면 됩니다.

## 조직도 (2026-11-18)

| 구분 | 조직 | 영문 | 하위 팀 |
|---|---|---|---|
| 직속 1실 | 자산형성실 | Wealth Strategy Office | 파킹통장 · 주거 · 장기 포트폴리오 |
| 그룹 | 재테크그룹 | Financial Tech Group | 청약운용팀 · 주식운용팀 · 리셀·프로모션팀 |
| 그룹 | 라이프매니지먼트그룹 | Life Management Group | 아침 브리핑 · 데이트 코스 · 구독 정리 |
| 그룹 | 뉴미디어스튜디오 | New Media Studio | 잡식공룡 AI 쇼츠 |
| 그룹 | 시스템·대외협력그룹 | System & Alliance Group | B/M·교류팀 · 허브 UI·UX 고도화팀 · 모니터링·리포팅팀 |
| 그룹 | 애슬레틱그룹 | Athletic & Wellness Group | 수영팀(사내 임직원 수영강습) · 헬스팀(독학 분할 루틴) |
| 그룹 | 자기개발그룹 | Self-Development Group | 영어 스피킹팀(유튜브 팟캐스트 · 목표 프리토킹) · 자격증팀(취득 준비 · 종목 확정 대기) |

카드를 누르면 상세 시트가 열리고, 하위 팀이 있는 그룹은 팀별 내용까지 이어서 보입니다.
