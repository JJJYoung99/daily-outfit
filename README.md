# 내일의 코디

Acloset 옷장에 등록한 내 옷으로 매일 밤 10시쯤 내일 코디를 골라 보여주는 페이지예요.

👉 **https://jjjyoung99.github.io/daily-outfit/**

## 어떻게 돌아가나요
1. **밤 9시 50분쯤**: Claude 클라우드 루틴이 내일 날씨, 구글 캘린더 일정(TPO), 유튜브·핀터레스트·매거진 트렌드를 보고
   `closet/`의 내 옷 중에서 코디를 골라 `days/<날짜>/day.json`을 커밋해요. 지시서는 [ROUTINE.md](ROUTINE.md).
2. **커밋되면 바로**: GitHub Actions가 옷 사진을 합쳐 코디 이미지를 만들고 `docs/`를 GitHub Pages로 올려요.
3. **밤 10시 40분 백업**: 루틴이 실패한 날엔 날씨만 보고 규칙대로 골라 페이지를 채워요(일정은 반영 안 됨).

컴퓨터가 꺼져 있어도 GitHub 서버와 Claude 클라우드에서 돌아가요.

## 스타일 기준
모던, 무채색 위주. 포인트 컬러는 코디 전체에서 하나까지.

## 옷장 업데이트
Acloset에 새 옷을 추가했다면 Mac의 Claude에게 "옷장 동기화해줘"라고 하면 돼요.
`scripts/import_closet.py`가 Acloset 화면 캡처를 아이템 사진과 `closet/closet.json`으로 바꿔요.

## 직접 다시 돌리기
Actions 탭 → "내일 코디 페이지" → Run workflow.
