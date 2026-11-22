#!/usr/bin/env python3
"""Headless render check for the hub (no browser needed).

Runs the page's inline scripts against a minimal DOM stub in QuickJS and
prints what the key containers end up containing, plus the result of the
interactive parts (결재/퀴즈 정답 공개, 영어 뜻 보기, 조직 상세 시트).
Works for both hub.html (data inlined) and index.html (data supplied here).

Usage: python3 render_check.py [hub.html|index.html] [--brief]
"""
import json
import pathlib
import re
import sys

import quickjs

HERE = pathlib.Path(__file__).resolve().parent
target = HERE / (sys.argv[1] if len(sys.argv) > 1 else "hub.html")
brief = "--brief" in sys.argv

html = target.read_text(encoding="utf-8")
scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
data_json = (HERE / "data.json").read_text(encoding="utf-8")

PRE = r"""
var __els = {};
var __cache = {};
function mkEl(sel){
  var el = {
    _sel: sel, innerHTML: "", textContent: "", hidden: false, href: "", style: {},
    dataset: {}, _listeners: {},
    classList: { _s: {},
      add: function(c){ this._s[c] = 1; },
      remove: function(c){ delete this._s[c]; },
      toggle: function(c, on){ if (on === undefined) { this._s[c] ? delete this._s[c] : this._s[c] = 1; } else if (on) { this._s[c] = 1; } else { delete this._s[c]; } },
      contains: function(c){ return !!this._s[c]; }
    },
    setAttribute: function(k, v){ this[k] = v; },
    getAttribute: function(k){ return this[k]; },
    addEventListener: function(ev, fn){ (this._listeners[ev] = this._listeners[ev] || []).push(fn); },
    appendChild: function(){}
  };
  __els[sel] = el;
  return el;
}
function el(sel){ return __els[sel] || mkEl(sel); }
/* 같은 클래스의 요소를 등록된 컨테이너들의 innerHTML에서 찾아, 같은 순서·같은 태그면 같은 객체를 돌려준다 */
function findAll(cls){
  var out = [], idx = 0, re = /<[a-zA-Z][^>]*>/g, k;
  for (k in __els){
    var h = __els[k].innerHTML || "";
    if (!h) continue;
    re.lastIndex = 0;
    var m;
    while ((m = re.exec(h))){
      var tag = m[0];
      var cm = tag.match(/class="([^"]*)"/);
      if (!cm) continue;
      if (cm[1].split(/\s+/).indexOf(cls) < 0) continue;
      var key = cls + "#" + idx + "|" + tag, e = __cache[key];
      if (!e){ e = mkEl("." + cls + "#" + idx); __cache[key] = e; }
      e.dataset = {};
      var d, dr = /data-([a-zA-Z-]+)="([^"]*)"/g;
      while ((d = dr.exec(tag))) e.dataset[d[1].replace(/-([a-z])/g, function(_, c){ return c.toUpperCase(); })] = d[2];
      out.push(e);
      idx++;
    }
  }
  return out;
}
function fire(elm, ev){
  if (!elm) return 0;
  var ls = elm._listeners[ev] || [];
  for (var i = 0; i < ls.length; i++) ls[i]();
  return ls.length;
}
var document = {
  documentElement: { _attrs: {}, setAttribute: function(k, v){ this._attrs[k] = v; }, getAttribute: function(k){ return this._attrs[k]; } },
  querySelector: function(sel){ return el(sel); },
  querySelectorAll: function(sel){
    if (sel.charAt(0) === "." && sel.indexOf("#") < 0) return findAll(sel.slice(1));
    return [];
  },
  addEventListener: function(){}
};
var window = {
  __INLINE_DATA__: null,
  matchMedia: function(){ return { matches: false }; },
  scrollTo: function(){},
  addEventListener: function(){}
};
var localStorage = { _d: {}, getItem: function(k){ return this._d[k] || null; }, setItem: function(k, v){ this._d[k] = v; } };
var setTimeout = function(fn){ return 0; };
var setInterval = function(){ return 0; };
var clearTimeout = function(){};
var Intl = { DateTimeFormat: function(){ return { format: function(){ return "2026-11-18"; } }; } };
"""

POST = r"""
var __OUT = (function(){
  var out = {};
  ["#service","#todayLabel","#footAt","#clock","#decCnt","#mktAt","#qpos","#ppos",
   "#deptCnt","#staffCnt","#govCnt","#trialCnt","#quizCnt","#moneyCnt","#opCnt",
   "#engineAt","#subAt","#rmCnt","#auditCnt","#fitAt"].forEach(function(s){
    out[s] = el(s).textContent;
  });
  ["#hero","#market","#decisions","#life","#banners","#kpis","#flow","#gov","#staff","#depts",
   "#bSum","#opSum","#ops","#report","#alliance","#ai3","#ai3time","#ai3week","#money",
   "#engine","#sub","#roadmap","#audit","#fit"].forEach(function(s){ out[s] = el(s).innerHTML; });

  /* --- v5: 재테크 실전 엔진 --- */
  out["engine.leverageLadder"] = (el("#engine").innerHTML.match(/lcard/g) || []).length;
  out["engine.exits"] = ((el("#engine").innerHTML.match(/익절/g) || []).length);
  out["engine.parking"] = el("#engine").innerHTML.indexOf("파킹") >= 0;
  out["engine.channels"] = el("#engine").innerHTML.indexOf("기화가거") >= 0 && el("#engine").innerHTML.indexOf("인사이트레이더") >= 0;
  out["sub.score"] = ((el("#sub").innerHTML.match(/<div class="xv">(\d+)<small>\/(\d+)/) || [])[0] || "");
  out["sub.cash"] = el("#sub").innerHTML.indexOf("2,475만") >= 0;
  out["roadmap.tracks"] = (el("#roadmap").innerHTML.match(/class="row"/g) || []).length;
  out["roadmap.gowi"] = el("#roadmap").innerHTML.indexOf("고향사랑기부") >= 0;
  out["audit.grade"] = ((el("#audit").innerHTML.match(/class="agrade">([^<]*)/) || ["", ""])[1] || "");
  out["audit.bars"] = (el("#audit").innerHTML.match(/class="arow"/g) || []).length;
  var __chh = el("#depts").innerHTML + el("#decisions").innerHTML + el("#banners").innerHTML + el("#staff").innerHTML;
  var __bare = __chh.split("구 호러트래커").join("");
  out["channel"] = {
    renamed: __chh.indexOf("이슈트래커") >= 0,
    bareOldLeft: __bare.indexOf("호러트래커") >= 0,
    historyMark: __chh.indexOf("구 호러트래커") >= 0,
    host: document.querySelector("#depts").innerHTML.indexOf("잡식공룡") >= 0
  };
  out["decisions.noCmong"] = el("#decisions").innerHTML.indexOf("크몽") < 0;

  /* --- v10: 대기업형 스태프·사업부 체제 --- */
  var sh = el("#staff").innerHTML;
  out["staff.cards"] = (sh.match(/class="office"/g) || []).length;
  out["staff.names"] = ["자산·리스크감사실", "법무·준법감시실", "경영기획·신사업실"].every(function(n){ return sh.indexOf(n) >= 0; });
  out["staff.legalScopes"] = (sh.match(/class="osrow"/g) || []).length;
  out["gov.lanes"] = (el("#gov").innerHTML.match(/class="gvlane"/g) || []).length;
  out["gov.model"] = el("#gov").innerHTML.indexOf("스태프·사업부 체제") >= 0;
  out["dept.divisions"] = (el("#depts").innerHTML.match(/class="dept/g) || []).length;
  out["dept.teamChips"] = (el("#depts").innerHTML.match(/class="gchip"/g) || []).length;
  out["org.teams"] = (function(){ var dd = window.__INLINE_DATA__ || {}, n = 0;
    ((dd.org || {}).groups || []).forEach(function(g){ n += (g.teams || []).length; }); return n; })();
  out["legal.today"] = el("#legal").innerHTML.indexOf("개구리 소년") >= 0;
  out["legal.advisorLine"] = el("#legal").innerHTML.indexOf("고문단 6인") >= 0;
  out["adv.cards"] = (el("#advisors").innerHTML.match(/class="adv"/g) || []).length;
  var pairs = ["금융·투자사업본부", "뉴미디어·IP사업본부", "라이프·웰니스사업본부", "시스템·R&D사업본부", "자산·리스크감사실", "법무·준법감시실"];
  var advHtml = el("#advisors").innerHTML.replace(/&amp;/g, "&");
  out["adv.pairsAll"] = pairs.every(function(p){ return advHtml.indexOf(p) >= 0; });
  out["adv.crossCheck"] = advHtml.indexOf("경영기획·신사업실") >= 0;
  /* v10.2: 본부·팀 명칭 통일 — 새 이름이 전부 떠 있고 옛 이름은 남지 않았는지 (상세 시트 모은 뒤 맨 끝에서 판정) */
  var newTeams = ["준법검수팀", "신사업발굴팀", "주식·모의투자운용팀", "청약·부동산운용팀", "리셀·프로모션팀",
    "쇼츠기획·이슈팀", "쇼츠제작·아트팀", "인스타툰·굿즈팀",
    "일상·주거관리팀", "커리어·채용모니터링팀", "피트니스·수영팀", "여행특가모니터링팀",
    "플랫폼·자동화팀", "대외협력·3AI협업팀"];
  /* 2026-11-20 통폐합으로 사라진 이름 — 화면에 다시 나오면 실패 */
  var oldTeams = ["호러트래커 소재·기획팀", "호러트래커 제작·편집팀", "이모티콘·스티커팀", "인스타툰팀",
    "이모티콘제작팀", "디지털 굿즈팀", "일상·주거팀", "수영팀", "헬스팀", "영어 스피킹팀", "자격증팀",
    "허브 UI/UX·자동화 엔진팀", "외부 채널·네트워크팀", "법무·컴플라이언스팀", "아이디어뱅크·부업발굴팀",
    /* 2026-11-22 14팀 통폐합으로 사라진 이름 */
    "주식운용팀", "모의투자운용팀", "쇼츠기획팀", "쇼츠제작팀", "수석시나리오팀", "엔터테인먼트이슈팀",
    "비주얼아트디자인팀", "인스타툰제작팀", "디지털굿즈팀", "수영강습팀", "피트니스팀", "어학스피킹팀",
    "자격증취득팀", "플랫폼UX·자동화팀", "대외협력·채널팀", "모니터링·리포팅팀"];
  var __sheetHTML = "";
  out["loop.steps"] = (el("#loop").innerHTML.match(/class="lstep"/g) || []).length;
  out["loop.items"] = (el("#loop").innerHTML.match(/class="fbrow"/g) || []).length;

  /* --- v13.6: 3AI 협업 본부별 역할 · 예약업무 시간표 --- */
  out["ai3.divisions"] = (el("#ai3").innerHTML.match(/class="op"/g) || []).length;
  out["ai3.times"] = (el("#ai3time").innerHTML.match(/class="op"/g) || []).length;
  out["ai3.weekly"] = (el("#ai3week").innerHTML.match(/class="op"/g) || []).length;
  out["ai3.slots"] = ["08:05", "16:00", "16:30", "17:00", "21:00"].every(function(t){ return el("#ai3time").innerHTML.indexOf(t) >= 0; });
  out["ai3.divisionNames"] = ["재테크", "디지털굿즈", "라이프", "뉴미디어"].every(function(n){ return el("#ai3").innerHTML.indexOf(n) >= 0; });

  /* --- v7: 사이클 지수투자 판정 --- */
  var cy = el("#cycle").innerHTML;
  out["cycle.phase"] = ((cy.match(/class="cp1">([^<]*)/) || ["", ""])[1] || "");
  out["cycle.score"] = ((cy.match(/class="cp2">([^<]*)/) || ["", ""])[1] || "");
  out["cycle.rows"] = (cy.match(/class=\"cycrow\"/g) || []).length;
  out["cycle.axes"] = (cy.match(/class=\"xcell\"/g) || []).length;
  out["cycle.action"] = cy.indexOf("오늘의 권고") >= 0;
  out["cycle.counter"] = cy.indexOf("고문 반론") >= 0;
  out["cycle.gate"] = cy.indexOf("1차선") >= 0;
  out["cycle.legal"] = cy.indexOf("자동 주문이 아닙니다") >= 0;
  out["cycle.at"] = el("#cycAt").textContent;

  /* --- v10.3: 오늘의 트레이닝 --- */
  var fh = el("#fit").innerHTML;
  out["fit.days"] = (fh.match(/class="wday /g) || []).length;
  out["fit.todayOn"] = (fh.match(/class="wday gym on"/) || []).length;
  out["fit.correct"] = (fh.match(/class="wc"/g) || []).length;
  out["fit.ramp"] = fh.indexOf("1~2주차") >= 0;
  out["fit.swimRule"] = fh.indexOf("볼륨 -20%") >= 0;
  out["fit.items"] = (fh.match(/· /g) || []).length;
  out["fit.at"] = el("#fitAt").textContent;

  /* --- 지운 항목(주거 청약 건·이어폰 배송 건)의 흔적이 남아 있지 않은지 --- */
  out["decisions.count"] = (el("#decisions").innerHTML.match(/class="dnum"/g) || []).length;
  var __d = window.__INLINE_DATA__ || {};
  var __ids = (__d.board || []).map(function(t){ return t.id; });
  out["cleanup.boardIds"] = !(__ids.indexOf("b34b") >= 0 || __ids.indexOf("b15") >= 0 || __ids.indexOf("b18") >= 0);
  out["cleanup.cards"] = !__d.subscription && !(__d.today && __d.today.life && __d.today.life.apply);
  /* v13: 크몽 생산직 전자책은 의도적으로 「보류」라 b41과 그 알림만 검사에서 뺍니다. */
  out["board.hold"] = (__d.board || []).filter(function(t){ return t.status === "hold"; }).map(function(t){ return t.id + ":" + t.title; }).join(",");
  out["board.holdFilter"] = el("#filters").innerHTML.indexOf("보류") >= 0;
  var __traceD = JSON.parse(JSON.stringify(__d));
  if (__traceD.board) __traceD.board = __traceD.board.filter(function(t){ return t.status !== "hold"; });
  __traceD.alerts = (__traceD.alerts || []).filter(function(a){ return (a.text || "").indexOf("생산직 전자책") < 0; });
  var __pat = new RegExp("\\uBCF4\\uB214|\\uC0E5\\uC988", "i");
  var __trace = JSON.stringify(__traceD) +
    ["#hero","#decisions","#life","#banners","#sub","#board","#advisors","#depts","#staff"].map(function(s){ return el(s).innerHTML; }).join("");
  out["cleanup.textTrace"] = __pat.test(__trace);
  out["sub.emptyHint"] = el("#sub").innerHTML.indexOf("판정 중인 공고가 없습니다") >= 0;

  /* --- 오늘의 1분 학습: 퀴즈 --- */
  var opts = document.querySelectorAll(".qopt");
  out["quiz.choiceCount"] = opts.length;
  out["quiz.beforeReveal"] = el("#quiz").innerHTML.indexOf("qans") >= 0;
  fire(opts[0], "click");
  var qh = el("#quiz").innerHTML;
  out["quiz.revealed"] = qh.indexOf("qans") >= 0;
  out["quiz.verdict"] = (qh.match(/<div class="qh">([^<]*)<\/div>/) || ["", ""])[1];
  out["quiz.marked"] = qh.indexOf("qopt ok") >= 0 ? "정답 보기 표시됨" : "표시 없음";
  out["quiz.explanation"] = ((qh.match(/<div class="qexp">([^<]*)<\/div>/) || ["", ""])[1] || "").slice(0, 70);
  var q1 = el("#quiz").innerHTML;
  fire(el("#qnext"), "click");
  out["quiz.nextChanged"] = el("#quiz").innerHTML !== q1;
  out["quiz.nextQuestion"] = ((el("#quiz").innerHTML.match(/<div class="qq">Q\. ([^<]*)/) || ["", ""])[1] || "").slice(0, 42);
  out["quiz.nextReset"] = el("#quiz").innerHTML.indexOf("qans") < 0 ? "해설 접힘" : "해설 남음";

  /* --- 오늘의 1분 학습: 영어 표현 --- */
  out["phrase.hasPronunciation"] = el("#phrase").innerHTML.indexOf("phpron") >= 0;
  out["phrase.word"] = ((el("#phrase").innerHTML.match(/<div class="phex">([^<]*)/) || ["", ""])[1] || "");
  out["phrase.koHiddenBefore"] = el("#phrase").innerHTML.indexOf("phko") < 0;
  fire(el("#btnKo"), "click");
  out["phrase.koShownAfter"] = el("#phrase").innerHTML.indexOf('class="phko"') >= 0;
  out["phrase.koText"] = ((el("#phrase").innerHTML.match(/<div class="phko">([^<]*)/) || ["", ""])[1] || "").slice(0, 40);
  fire(el("#btnSpeak"), "click");
  out["phrase.speakToast"] = el("#toast").textContent;

  /* --- v10.6: 두 트랙 판단 · 모의투자 원장 카드 --- */
  var trkH = el("#tracks").innerHTML, papH = el("#paper").innerHTML;
  out["tracks.rendered"] = trkH.length > 200;
  out["tracks.signals"] = (trkH.match(/BUY_T\d|WAIT/g) || []).join(",");
  out["tracks.hasFunds"] = trkH.indexOf("퇴직금 트랙") >= 0 && trkH.indexOf("개인연금 트랙") >= 0;
  out["tracks.hasNext"] = trkH.indexOf("다음 ") >= 0;
  out["paper.rendered"] = papH.length > 150;
  out["paper.books"] = (papH.match(/Book [AB]/g) || []).join(",");
  out["paper.hasDiff"] = papH.indexOf("분할–올인") >= 0;
  out["paper.noAmounts"] = !/\d{2,3},\d{3},\d{3}원/.test(papH + trkH);

  /* --- v11: SOXL 추이·매수 판정 --- */
  var sxH = el("#soxl").innerHTML;
  out["soxl.rendered"] = sxH.length > 200;
  out["soxl.verdict"] = ((sxH.match(/class="cp1">([^<]*)/) || ["", ""])[1] || "");
  out["soxl.cells"] = (sxH.match(/class="xcell"/g) || []).length;
  out["soxl.lines"] = (sxH.match(/class="cycrow"/g) || []).length;
  out["soxl.conds"] = (sxH.match(/class="ch"/g) || []).length;
  out["soxl.legal"] = sxH.indexOf("자동 주문이 아닙니다") >= 0;
  out["soxl.at"] = el("#soxlAt").textContent;

  /* --- 조직 상세 시트 --- */
  var staffCards = document.querySelectorAll(".office");
  out["staffCount"] = staffCards.length;
  for (var s = 0; s < staffCards.length; s++){
    fire(staffCards[s], "click");
    __sheetHTML += el("#sheetTeams").innerHTML;
    out["sheet:staff" + s] = el("#sheetTitle").innerHTML + " || teams=" + el("#sheetTeams").innerHTML.length +
      " || " + ((el("#sheetTeams").innerHTML.match(/steams-head">([^<]*)/) || ["", "—"])[1] || "—");
    if (s === 0) out["sheet:staffDetails"] = el("#sheetList").innerHTML.slice(0, 60);
  }
  var groups = document.querySelectorAll(".dept");
  out["deptCount"] = groups.length;
  for (var i = 0; i < groups.length; i++){
    fire(groups[i], "click");
    __sheetHTML += el("#sheetTeams").innerHTML;
    out["sheet:group" + i] = el("#sheetTitle").innerHTML + " || teams=" + el("#sheetTeams").innerHTML.length +
      " || " + ((el("#sheetTeams").innerHTML.match(/steams-head">([^<]*)/) || ["", ""])[1] || "—");
  }
  var dh = (el("#depts").innerHTML + el("#staff").innerHTML + __sheetHTML).replace(/&amp;/g, "&");
  out["names.newTeamsMissing"] = newTeams.filter(function(n){ return dh.indexOf(n) < 0; });
  /* 새 이름 안에 들어 있는 옛 이름(피트니스·수영팀 ⊃ 수영팀 등)은 오탐이라 건너뜁니다 */
  out["names.oldTeamsLeft"] = oldTeams.filter(function(n){
    if (newTeams.some(function(m){ return m.indexOf(n) >= 0; })) return false;
    return dh.indexOf(n) >= 0;
  });
  out["names.divisionsAll"] = ["금융·투자사업본부", "뉴미디어·IP사업본부", "라이프·웰니스사업본부", "시스템·R&D사업본부"]
    .every(function(n){ return el("#depts").innerHTML.replace(/&amp;/g, "&").indexOf(n) >= 0; });
  return out;
})();
"""

if len(scripts) == 1:
    body = "window.__INLINE_DATA__ = " + data_json + ";\n" + scripts[0]
else:
    body = scripts[0] + "\n" + scripts[1]

ctx = quickjs.Context()
res = ctx.eval(PRE + "\n" + body + "\n" + POST + "\n;JSON.stringify(__OUT);")
out = json.loads(res)

if brief:
    for k, v in out.items():
        if k.startswith("sheet:"):
            print(k, "->", v[:150])
        else:
            print(k, "->", str(v).replace("\n", " ")[:120])
else:
    for k, v in out.items():
        print("=" * 8, k)
        print(v)
