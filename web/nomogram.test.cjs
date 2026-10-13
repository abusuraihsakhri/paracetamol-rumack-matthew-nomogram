const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const {lineAt, evaluate} = require("./nomogram.js");
const base={hours:8, concentration:75, pattern:"acute", timeKnown:true, delayedAbsorption:false};
test("reference line points",()=>{
  for(const [h,c] of [[4,150],[8,75],[12,37.5],[16,18.75],[20,9.375],[24,4.6875]]) assert.equal(lineAt(h),c);
});
test("on-line counts as above",()=>assert.equal(evaluate(base).status,"at_or_above_treatment_line"));
test("below line",()=>assert.equal(evaluate({...base,concentration:20}).status,"below_treatment_line"));
test("ineligible history yields no threshold",()=>{
  for(const change of [{hours:3},{hours:25},{pattern:"repeated"},{pattern:"unknown"},{pattern:"modified_release"},{timeKnown:false}]){
    const result=evaluate({...base,...change});
    assert.equal(result.status,"not_applicable");assert.equal(result.line,null);
  }
});
test("rejects invalid numbers",()=> {
  for(const n of [NaN,Infinity,-1,"",null]) assert.throws(()=>evaluate({...base,concentration:n}));
});
test("delayed absorption warning",()=>assert.ok(evaluate({...base,delayedAbsorption:true}).cautions.length));
test("inline browser UI script parses",()=>{
  const html=fs.readFileSync(path.join(__dirname,"index.html"),"utf8");
  const scripts=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)];
  assert.ok(scripts.length>0);
  for(const script of scripts) new vm.Script(script[1]);
});
