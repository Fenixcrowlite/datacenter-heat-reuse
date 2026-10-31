"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const {authorize}=require("../broker.cjs");
test("viewer is strictly read-only",()=>{
 assert.equal(authorize("viewer","subscribe","dchr/v09/sim/#"),true);
 assert.equal(authorize("viewer","subscribe","dchr/v09/sim/meta"),true);
 for(const topic of ["dchr/v09/sim/value/T_pool_C","dchr/v09/sim/status","dchr/v09/sim/command/PLC",
                    "dchr/v09/sim/value/STOP"]){
   assert.equal(authorize("viewer","publish",topic),false);
 }
});
test("exporter is strictly write-only to synthetic data",()=>{
 assert.equal(authorize("exporter","publish","dchr/v09/sim/value/T_pool_C"),true);
 assert.equal(authorize("exporter","subscribe","dchr/v09/sim/#"),false);
 for(const topic of ["dchr/v09/sim/command/PLC","dchr/v09/real/value/PLC",
                    "dchr/v09/sim/#","$SYS/broker/clients","dchr/v09/sim/control"]){
  assert.equal(authorize("exporter","publish",topic),false);
 }
});
test("anonymous, wildcard escape and role confusion are denied",()=>{
 for(const role of [null,"","guest","reader","exporter"]){
  assert.equal(authorize(role,"subscribe","#"),false);
  assert.equal(authorize(role,"subscribe","dchr/#"),false);
 }
 for(const role of [null,"guest","viewer"]){
  assert.equal(authorize(role,"publish","dchr/v09/sim/value/T_pool_C"),false);
 }
});
