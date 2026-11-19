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
   "#deptCnt","#officeCnt","#trialCnt","#quizCnt","#moneyCnt","#opCnt",
   "#engineAt","#subAt","#rmCnt","#auditCnt"].forEach(function(s){
    out[s] = el(s).textContent;
  });
  ["#hero","#market","#decisions","#life","#banners","#kpis","#flow","#office","#depts",
   "#bSum","#opSum","#ops","#report","#alliance","#money",
   "#engine","#sub","#roadmap","#audit"].forEach(function(s){ out[s] = el(s).innerHTML; });

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
  out["horror"] = {
    org: document.querySelector("#depts").innerHTML.indexOf("호러트래커") >= 0,
    old: document.querySelector("#depts").innerHTML.indexOf("잡식공룡") >= 0,
    decision: el("#decisions").innerHTML.indexOf("호러트래커") >= 0
  };

  /* --- v6: 법무팀 + 고문단 --- */
  out["legal.cardName"] = el("#legalCard").innerHTML.indexOf("법무·컴플라이언스팀") >= 0;
  out["legal.scopes"] = (el("#legalCard").innerHTML.match(/class="osrow"/g) || []).length;
  out["legal.today"] = el("#legal").innerHTML.indexOf("개구리 소년") >= 0;
  out["legal.advisorLine"] = el("#legal").innerHTML.indexOf("고문단 6인") >= 0;
  out["adv.cards"] = (el("#advisors").innerHTML.match(/class="adv"/g) || []).length;
  var pairs = ["재테크그룹", "뉴미디어스튜디오", "라이프매니지먼트그룹", "시스템·대외협력그룹", "애슬레틱", "자산형성실"];
  out["adv.pairsAll"] = pairs.every(function(p){ return el("#advisors").innerHTML.indexOf(p) >= 0; });
  out["loop.steps"] = (el("#loop").innerHTML.match(/class="lstep"/g) || []).length;
  out["loop.items"] = (el("#loop").innerHTML.match(/class="fbrow"/g) || []).length;
  out["sub.rejected"] = el("#sub").innerHTML.indexOf("반려 완료") >= 0;

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

  /* --- 반려한 청약 건이 대기·알림에 남아 있지 않은지 --- */
  out["decisions.count"] = (el("#decisions").innerHTML.match(/class="dnum"/g) || []).length;
  out["decisions.bonum"] = el("#decisions").innerHTML.indexOf("보눔") >= 0;
  out["alerts.bonum"] = el("#banners").innerHTML.indexOf("보눔") >= 0;
  out["life.rejected"] = el("#life").innerHTML.indexOf("반려 완료") >= 0;

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

  /* --- 조직 상세 시트 --- */
  fire(el("#office"), "click");
  out["sheet:office"] = el("#sheetTitle").innerHTML + " || teams=" + el("#sheetTeams").innerHTML.length +
    " || " + el("#sheetList").innerHTML.slice(0, 60);
  var groups = document.querySelectorAll(".dept");
  out["deptCount"] = groups.length;
  for (var i = 0; i < groups.length; i++){
    fire(groups[i], "click");
    out["sheet:group" + i] = el("#sheetTitle").innerHTML + " || teams=" + el("#sheetTeams").innerHTML.length +
      " || " + ((el("#sheetTeams").innerHTML.match(/steams-head">([^<]*)/) || ["", ""])[1] || "—");
  }
  fire(el("#legalCard"), "click");
  out["sheet:legal"] = el("#sheetTitle").innerHTML + " || details=" + el("#sheetList").innerHTML.length;
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
