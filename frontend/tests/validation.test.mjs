import test from 'node:test';
import assert from 'node:assert/strict';
import {isAnalysis} from '../src/validation.ts';
const valid=()=>({origin:{label:'Dallas',lat:32.8,lon:-96.8},destination:{label:'Atlanta',lat:33.7,lon:-84.4},routes:[{id:'route-1',distance_miles:783,duration_seconds:50940,geometry:{type:'LineString',coordinates:[[-96.8,32.8],[-84.4,33.7]]}}],warnings:[]});
test('accepts a valid route analysis response',()=>assert.equal(isAnalysis(valid()),true));
test('rejects missing routes and invalid coordinate geometry',()=>{const a=valid();a.routes=[];assert.equal(isAnalysis(a),false);const b=valid();b.routes[0].geometry.coordinates[1]=[999,33];assert.equal(isAnalysis(b),false)});
test('rejects missing location coordinates and non-finite distances',()=>{const a=valid();a.origin.lat=NaN;assert.equal(isAnalysis(a),false);const b=valid();b.routes[0].distance_miles=Infinity;assert.equal(isAnalysis(b),false)});
test('rejects malformed warnings',()=>{const a=valid();a.warnings=[null];assert.equal(isAnalysis(a),false)});
