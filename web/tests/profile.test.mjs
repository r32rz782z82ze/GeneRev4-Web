import {test} from "node:test";
import assert from "node:assert/strict";
import {parseProfile, toCsv, toTxt, targetAt, EXAMPLE, asClock} from "../profile-core.mjs";
test("Nico CSV sentinel + steps", () => {
  const pts = parseProfile("999;header\r\n0;180\r\n60;195.5\r\n120;200\r\n");
  assert.deepEqual(pts,[{time:0,temp:180},{time:60,temp:195.5},{time:120,temp:200}]);
  assert.equal(targetAt(pts,59),180);
  assert.equal(targetAt(pts,60),195.5);
});
test("Nico TXT tN/TN pairs", () => {
  const pts = parseProfile("[t1=0]\n[T1=180]\n[t2=60]\n[T2=200]");
  assert.equal(pts.length,2);
  assert.equal(pts[1].temp,200);
});
test("roundtrips", () => {
  assert.deepEqual(parseProfile(toCsv(EXAMPLE)),EXAMPLE);
  assert.deepEqual(parseProfile(toTxt(EXAMPLE)),EXAMPLE);
});
test("invalid profiles refused", () => {
  for (const text of ["0;150\n0;180","0;300","-1;180","x;180","1;180\n0;190","", "[t1=0]"]) {
    assert.throws(() => parseProfile(text), undefined, text);
  }
});
test("time presentation", () => assert.equal(asClock(125),"02:05"));
