import type {Analysis} from './api';
/** Validate the minimum route-analysis contract before rendering map geometry. */
export function isAnalysis(value:unknown):value is Analysis {
 if(!value||typeof value!=='object')return false;
 const d=value as Partial<Analysis>;
 const location=(v:unknown)=>Boolean(v&&typeof v==='object'&&typeof (v as {label?:unknown}).label==='string'&&Number.isFinite((v as {lat?:unknown}).lat)&&Number.isFinite((v as {lon?:unknown}).lon));
 return Boolean(location(d.origin)&&location(d.destination)&&Array.isArray(d.routes)&&d.routes.length>0&&d.routes.every(r=>r&&typeof r.id==='string'&&Number.isFinite(r.distance_miles)&&r.distance_miles>=0&&Number.isFinite(r.duration_seconds)&&r.duration_seconds>=0&&r.geometry?.type==='LineString'&&Array.isArray(r.geometry.coordinates)&&r.geometry.coordinates.length>=2&&r.geometry.coordinates.every(p=>Array.isArray(p)&&p.length>=2&&Number.isFinite(p[0])&&Number.isFinite(p[1])&&p[0]>=-180&&p[0]<=180&&p[1]>=-90&&p[1]<=90))&&Array.isArray(d.warnings)&&d.warnings.every(w=>typeof w==='string'));
}
