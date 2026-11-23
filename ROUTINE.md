# 매일 밤 코디 루틴 (Claude가 읽는 지시서)

이 저장소에서 "내일" 입을 코디를 골라 `days/<내일 YYYY-MM-DD>/day.json`을 커밋한다.
푸시하면 GitHub Actions가 코디 이미지와 페이지(docs/)를 만들어 GitHub Pages에 올린다.
모든 글은 한국어로 쓴다. 내일 = 실행 시각(Asia/Seoul) 기준 다음 날.

## 사용자
- 남성, 서울 거주. 전공의라 평일 근무일엔 단정하고 편한 옷.
- **취향(가장 중요)**: 모던, 무채색(블랙·화이트·그레이·차콜·아이보리) 위주. 포인트 컬러는 코디 전체에서 **하나까지**.
  네이비·베이지·브라운·블루도 각각 한 색으로 센다. 여러 색이 섞인 코디는 고르지 않는다.

## 1. 내일 날씨
- (클라우드 환경에선 Open-Meteo가 막혀 있을 수 있다. 막히면 바로 WebSearch로 넘어간다.)
- `curl -s "https://api.open-meteo.com/v1/forecast?latitude=37.53&longitude=126.98&timezone=Asia%2FSeoul&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code&start_date=<내일>&end_date=<내일>"`
- 막히면 WebSearch로 "서울 내일 날씨"를 찾는다. 일정 장소가 서울 밖이면 그 지역 날씨를 쓴다.

## 2. 내일 TPO
- **먼저 `schedule/work.json`(근무 일정표)을 본다.** `work`에 내일 날짜가 있으면 근무일(`night`는 늦게 끝나는 날이라 퇴근길 추위를 감안), `covered` 기간 안인데 `work`에 없으면 휴일이다. 요일과 상관없이 이 표가 우선이다(주말 근무, 평일 휴무가 흔하다).
- 내일이 `covered` 밖이면 일정표가 없는 날이다. 아래 캘린더를 보고, 그것도 안 되면 요일로 추정하되 tpo.source에 "근무 일정표에 없는 날이라 추정했다"고 적는다.
- 근무일이어도 캘린더에 퇴근 후 약속이 있으면 함께 소화하는 코디로 고른다.
- Google Calendar 커넥터로 내일 00:00~모레 00:00 일정을 본다(list_events, 오프셋 없이).
- 일정을 보고 TPO를 정한다: 근무, 결혼식(하객룩), 학회/발표, 약속/데이트, 휴일 외출 등. 일정이 이어지면 하나의 코디로 다 소화하게 고른다.
- **공개 페이지다.** 일정 제목, 사람 이름, 정확한 장소(예식장 이름 등)는 절대 쓰지 않는다. "근무", "저녁 약속", "결혼식 → 데이트"처럼 일반화한다. 지역은 구 단위까지만.
- 캘린더에 접근할 수 없으면 평일=근무, 주말=휴일 외출로 정하고 tpo.source에 그렇게 적는다.

## 3. 트렌드 참고 (유튜브·핀터레스트)
- WebSearch 2~3번: TPO·계절·취향 키워드를 섞는다. 예: "11월 남자 하객룩 모노톤 유튜브", "pinterest men monochrome fall outfit", "남자 미니멀 출근룩 11월".
- 유튜브·핀터레스트 결과를 우선 보고, 없으면 패션 매거진(GQ, 에스콰이어, 엘르, 보그, W 코리아)이나 남성복 브랜드 가이드를 쓴다.
- 실제로 참고한 링크 2~4개를 refs에 넣는다. 지어낸 링크는 넣지 않는다.

## 4. 옷 고르기
- 옷장은 `closet/closet.json` (id, cat[top/bottom/outer/shoes/acc], name, brand, acloset_cat, desc, sub, color, sleeve, warmth 1~3, season(여름 전용이면 "summer"), formal 1~3, 신발·가방은 rain_ok).
  `name`은 Acloset에 저장된 브랜드 + 색상 + 카테고리로 만든 이름이다. 코디 제목(title), 설명(why), 메모(note)에서 옷을 가리킬 때는 반드시 이 `name`(또는 '브랜드 + 색 + 종류'로 줄인 형태)을 쓴다. 브랜드 없이 "화이트 셔츠"처럼만 쓰지 않는다.
  아이템 사진은 `closet/items/<id>.jpg`. 애매하면 Read로 사진을 직접 본다.
- 코디 1개 = 상의 1~2개(셔츠+니트 레이어드 가능) + 하의 1 + 신발 1 + (필요하면) 아우터 1 + 가방/액세서리 0~2.
- `season: "summer"`인 옷(얇은 여름 바지 등)은 평균기온 20° 미만이면 고르지 않는다.
- 날씨 기준: 평균기온 22°↑ 반팔, 15°↓ 니트·아우터, 8°↓ warmth 3 아우터. 강수 50%↑이면 rain_ok=false 신발 금지. 일교차 8°↑이면 벗기 쉬운 레이어드.
- TPO별 formal: 하객·학회 3, 근무·데이트 2, 휴일 1~2. 한 코디 안에서 formal 차이는 1 이하. sport·sandal 신발은 운동·여름 휴일에만.
- 최근 7일(`days/`)에 추천(pick)한 상의·아우터는 가능하면 반복하지 않는다.
- **`exclude`가 있는 옷은 절대 고르지 않는다** (sport=운동복, discarded=버림, not_arrived=아직 배송 전. 도착하면 사용자가 알려줄 때 exclude를 지운다).
- `casual_only: true` 니트(DRAW FIT·ZARA·더니트컴퍼니·무신사 스탠다드 등 저가 니트)는 아주 편한 휴일 코디에만 쓴다. 니트는 브라운야드 이상급(포터리·토니웩·아트이프액츠·미나브·쿠어·스톤아일랜드·폴로·렉토 등)을 우선한다.
- **니트 이너 + 니트 가디건/니트 집업 조합은 금지.** 가디건·니트 집업 안에는 셔츠나 티셔츠를 입힌다. 니트는 코트·재킷 안에 입힌다.
- 미나브 니트는 등급을 낮춰 casual_only다. 더니트컴퍼니·artifact·NONBLANK는 괜찮다.
- **출근 코디 신발**: `work_low: true` 신발(완전 러닝화 등 운동화, 끈 구두·윙팁·캡토 같은 구두, 발렌시아가·투스페이스처럼 부피가 큰 신발 — 병원 신발장이 작음)은 평일 출근 코디에서 후순위다. 스니커즈·로퍼·슬립온을 먼저 쓰고, 다른 선택지가 없거나 격식 있는 일정이 있을 때만 쓴다. 테니스화(ADIDAS 화이트 니트 테니스화)는 exclude라 쓰지 않는다.
- `low_priority: true` 옷(H&M 등 후순위 브랜드)은 다른 선택지가 없을 때만 쓴다. H&M은 앞으로 새 옷이 들어와도 후순위로 둔다.
- `comfort: "low"` 신발(투스페이스 블랙 레더 스니커즈: 크고 불편함, 사용자가 평발)은 다른 선택지가 없을 때만 쓴다.
- 여행 코디는 짐을 최소로: 아우터·바지·신발은 이틀 같은 것, 상의만 1벌 추가하는 식으로 짠다. 여행 날은 day.json에 `"no_auto": true`를 넣어 챙기지 않은 옷이 자동 조합으로 나오지 않게 한다.
- **브랜드 믹스**: `closet/brands.json`의 tier를 본다(premium > designer > core > basic).
  코디마다 좋아하는 브랜드(premium·designer·core) 옷을 1개 이상 넣고, 추천 코디에는 designer나 premium을 1개 이상 넣는다.
  비싼 옷과 데일리 옷을 섞는다(예: 솔리드옴므 바지 + 쿠어 니트 + 기본 스니커즈). ZARA·SPAO·H&M·무신사 스탠다드 같은 basic만으로 코디를 채우지 않는다.
- **로테이션(안 입는 옷 없게)**: 먼저 `python3 scripts/usage.py <내일> <평균기온>`을 돌려 날씨에 맞는 옷 중 한 번도 추천 안 됐거나 오래 안 나온 옷을 본다.
  코디 3개 중 최소 2개에는 이 목록 상위(횟수 0 또는 가장 오래된) 옷을 하나 이상 넣는다. 같은 옷을 연달아 쓰지 말고 옷장 전체가 돌아가게 한다.
  단, 정리 후보(`style/report.json`의 clean)에 있는 옷은 억지로 넣지 않는다.
- "추천"(pick: true) 1개 + "대안" 2개(예: 추우면 코트 추가, 포인트 컬러 하나 버전, 결이 다른 조합). 서로 상의·아우터가 겹치지 않게 하면 좋다.
- 페이지의 "다른 코디 추천" 버튼은 이 코디들을 차례로 보여주고, 모자라는 만큼(총 6개까지) build.py가 같은 날씨·격식 규칙으로 자동 조합을 채운다.

## 5. day.json 쓰기
`days/2026-11-15/day.json`과 같은 형식:
```json
{"date":"YYYY-MM-DD","weekday":"월",
 "weather":{"place":"서울","summary":"흐림","low":8,"high":17,"rain":45,"note":"옷차림 포인트 2문장"},
 "tpo":{"label":"근무","source":"왜 이 TPO로 봤는지 한 문장(일반화)"},
 "outfits":[{"pick":true,"title":"화이트 셔츠 + 블랙 블레이저","why":"트렌드 근거 포함 2~3문장",
             "items":[{"id":"top-039","note":"이 아이템을 왜·어떻게 입는지 한 줄"}]},
            {"pick":false,"title":"...","why":"...","items":[{"id":"...","note":""}]}],
 "refs":[{"label":"매체 · 제목","url":"https://..."}]}
```
- 데이트 코스·장소 추천(plan)은 넣지 않는다. 코디만 다룬다.
- 모든 id가 closet.json에 있는지 확인한다: `python3 -c "import json;c={i['id'] for i in json.load(open('closet/closet.json'))};d=json.load(open('days/<날짜>/day.json'));print([x['id'] for o in d['outfits'] for x in o['items'] if x['id'] not in c])"` → `[]`이어야 한다.
- `pip install pillow -q && python3 scripts/build.py`로 한 번 빌드해 오류가 없는지 본다. 생성된 `docs/img/<날짜>-1.jpg`를 Read로 확인한다.

## 6. 커밋
- `git add days && git commit -m "Outfit for <날짜>"` (docs/는 커밋하지 않는다. Actions가 다시 만든다.)
- 먼저 `git push origin HEAD:refs/heads/main`을 시도한다. 거부되면(권한·브랜치 제한) `git push origin HEAD:refs/heads/outfit/<날짜>`로 올린다.
  outfit/ 브랜치로 올라오면 GitHub Actions가 days/를 main에 합치고 페이지를 만든 뒤 그 브랜치를 지운다. PR은 만들지 않는다.
- 이미 그 날짜 day.json이 있으면(백업이 먼저 돈 경우 등) 덮어쓴다. **단, `"locked": true`가 있으면 사용자가 정한 일정이므로 건드리지 말고 커밋 없이 끝낸다.**
- 마지막 메시지: "내일(M/D) 코디: <추천 제목> — x~y°, 강수 z%, <TPO>" 와 페이지 링크 https://jjjyoung99.github.io/daily-outfit/

## 저장한 코디 (favorites.json)
사용자가 마음에 든다고 한 코디는 favorites.json에 스냅샷으로 저장하고, build.py가 docs/favorites.html로 만든다. 루틴은 이 파일을 수정하지 않는다. 새 코디를 짤 때 저장된 조합의 색·아이템 구성을 취향 참고로 삼되 그대로 반복하지는 않는다.
