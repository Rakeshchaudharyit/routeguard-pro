import {isAnalysis} from './validation';
export type ForecastCoverage={analyzed:number;total:number;status:'complete'|'partial'|'unavailable'};
export type Route={id:string;name:string;distance_miles:number;duration_seconds:number;arrival_at:string;geometry:{type:'LineString';coordinates:number[][]};weather_status:string;risk_level?:string|null;recommended?:boolean;high_miles?:number;severe_miles?:number;no_travel_miles?:number;average_risk?:number|null;checkpoints?:Checkpoint[];forecast_coverage?:ForecastCoverage;unknown_miles?:number;timeline_base?:string};
export type Checkpoint={mile:number;lat:number;lon:number;eta:string;risk:string;wind_mph:number|null;rain_in_hr:number|null;snow_in_hr:number|null;reason?:string;timeline?:{hour:number;risk:string;wind_mph:number|null;rain_in_hr:number|null;snow_in_hr:number|null}[]};
export type Analysis={origin:{label:string;lat:number;lon:number};destination:{label:string;lat:number;lon:number};routes:Route[];warnings:string[];weather_analyzed:boolean;recommendation:string|null};
const API=import.meta.env.VITE_API_BASE_URL||'http://127.0.0.1:8010';
const TIMEOUT_MS=90000;
export class AnalysisError extends Error {
 constructor(message:string,public readonly kind:'timeout'|'network'|'server'|'invalid'|'cancelled'|'request',public readonly status?:number){super(message);this.name='AnalysisError'}
}
export async function analyzeRoute(payload:Record<string,unknown>,signal?:AbortSignal):Promise<Analysis>{
 const controller=new AbortController();
 let timedOut=false;
 const onAbort=()=>controller.abort();
 if(signal?.aborted)throw new AnalysisError('Analysis cancelled.','cancelled');
 signal?.addEventListener('abort',onAbort,{once:true});
 const timeout=setTimeout(()=>{timedOut=true;controller.abort()},TIMEOUT_MS);
 try{
  const res=await fetch(`${API}/api/routes/analyze/`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:controller.signal});
  const raw=await res.text();let data:unknown;
  try{data=JSON.parse(raw)}catch{throw new AnalysisError('The server returned an unreadable response. Please try again.','invalid',res.status)}
  if(!res.ok){const detail=data&&typeof data==='object'&&'error' in data&&typeof data.error==='string'?data.error:null;
   if(res.status>=500)throw new AnalysisError(detail||'The routing or weather service is temporarily unavailable. Please retry.','server',res.status);
   throw new AnalysisError(detail||'Please check the trip details and try again.','request',res.status);
  }
  if(!isAnalysis(data))throw new AnalysisError('Route analysis returned incomplete route information. Previous results were kept.','invalid',res.status);
  return data;
 }catch(err){
  if(err instanceof AnalysisError)throw err;
  if(timedOut)throw new AnalysisError('Route analysis timed out. Check your connection and try again.','timeout');
  if(signal?.aborted)throw new AnalysisError('Analysis cancelled.','cancelled');
  if(err instanceof TypeError)throw new AnalysisError('Cannot connect to the RouteGuard backend. Check that Django is running on port 8010.','network');
  throw new AnalysisError('Unable to complete route analysis. Please retry.','server');
 }finally{clearTimeout(timeout);signal?.removeEventListener('abort',onAbort)}
}
