#!/usr/bin/env python3
"""Headless render check for the hub (no browser needed).

Runs the page's inline scripts against a minimal DOM stub in QuickJS and
prints what the key containers end up containing. Works for both
hub.html (data inlined) and index.html (data supplied up front here).

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

PRE = """
var __els = {};
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
var document = {
  documentElement: { _attrs: {}, setAttribute: function(k, v){ this._attrs[k] = v; }, getAttribute: function(k){ return this._attrs[k]; } },
  querySelector: function(sel){ return el(sel); },
  querySelectorAll: function(sel){
    if (sel === ".dept") {
      var n = (el("#depts").innerHTML.match(/class="dept/g) || []).length;
      var out = [];
      for (var i = 0; i < n; i++) { var e = el(".dept#" + i); e.dataset.g = String(i); out.push(e); }
      return out;
    }
    if (sel === ".office") { return [el("#office")]; }
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

POST = """
var __OUT = (function(){
  var out = {};
  ["#service","#syncAt","#footAt","#clock","#deptCnt","#officeCnt","#trialCnt","#quizCnt","#moneyCnt","#opCnt"].forEach(function(s){
    out[s] = el(s).textContent;
  });
  ["#banners","#kpis","#flow","#office","#depts","#bSum","#opSum","#ops","#report","#alliance","#money"].forEach(function(s){
    out[s] = el(s).innerHTML;
  });
  var off = el("#office");
  (off._listeners.click || []).forEach(function(fn){ fn(); });
  out["sheet:office"] = el("#sheetTitle").innerHTML + " || " + el("#sheetTeams").innerHTML.length + " || " + el("#sheetList").innerHTML.slice(0, 80);
  function fireGroup(i){
    var g = el(".dept#" + i);
    (g._listeners.click || []).forEach(function(fn){ fn(); });
    return el("#sheetTitle").innerHTML + " || teams-html=" + el("#sheetTeams").innerHTML.length + " || head=" +
      (el("#sheetTeams").innerHTML.match(/steams-head">[^<]*/) || [""])[0];
  }
  for (var i = 0; i < 6; i++) { out["sheet:group" + i] = fireGroup(i); }
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
