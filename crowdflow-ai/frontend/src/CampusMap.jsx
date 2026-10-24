import React,{useEffect} from 'react'
import L from 'leaflet'
import {MapContainer,Polyline,CircleMarker,Tooltip,Popup,Rectangle,useMap} from 'react-leaflet'
import {MapPin,Layers} from 'lucide-react'

function Fit(){const map=useMap();useEffect(()=>{map.fitBounds([[0,0],[470,515]],{padding:[22,22]});const observer=new ResizeObserver(()=>{map.invalidateSize();map.fitBounds([[0,0],[470,515]],{padding:[22,22]})});observer.observe(map.getContainer());return()=>observer.disconnect()},[map]);return null}
const congestionColor=e=>e.closed?'#7e8791':e.congestion>1?'#de6452':e.congestion>.65?'#dfab49':'#64a889'
export default function CampusMap({state,route,onPathway}){
 const nodes=state?.graph?.nodes||[],edges=state?.graph?.edges||[]
 const locations=Object.fromEntries(nodes.map(n=>[n.id,n]))
 const highlighted=new Map()
 route?.routes?.filter(r=>r.pedestrians>0).forEach((r,i)=>r.pathways.forEach(pid=>highlighted.set(pid,['#176e55','#586dc1','#d59136','#9256b2','#008d9f','#c36475'][i%6])))
 return <div className="map-shell"><div className="map-top"><span><MapPin size={15}/> Meridian University <small>FICTIONAL CAMPUS</small></span><span><Layers size={14}/> {nodes.length} nodes · {edges.length} paths</span></div>
 <MapContainer crs={L.CRS.Simple} center={[230,260]} zoom={0} minZoom={-2} maxZoom={3} preferCanvas={false} attributionControl={false} className="campus-map"><Fit/>
 <Rectangle bounds={[[8,8],[447,502]]} pathOptions={{color:'#cfd7c6',weight:1,fillColor:'#f5f6ec',fillOpacity:1}}/>
 <Rectangle bounds={[[105,95],[185,170]]} pathOptions={{color:'#dce6cc',weight:0,fillColor:'#dce6cc',fillOpacity:.7}}><Tooltip sticky>Botanical garden</Tooltip></Rectangle>
 <Rectangle bounds={[[305,330],[395,455]]} pathOptions={{color:'#d4e4c4',weight:0,fillColor:'#d4e4c4',fillOpacity:.75}}><Tooltip sticky>Sports lawns</Tooltip></Rectangle>
 {edges.map(e=>{const a=locations[e.source],b=locations[e.target],color=e.closed?null:highlighted.get(e.id);return <Polyline key={e.id} positions={[[a.y,a.x],[b.y,b.x]]} pathOptions={{color:color||congestionColor(e),weight:color?7:Math.max(3,e.width*1.2),opacity:color?1:.72,dashArray:e.closed?'7 7':null}} eventHandlers={{click:()=>onPathway?.(e)}}><Popup><strong>{e.id} · {a.name} → {b.name}</strong><p>{e.distance} m · {e.width} m wide</p><p>{e.occupancy} / {e.capacity} comfort capacity · ceiling {e.hard_capacity}</p><p>Forecast {e.predicted.toFixed(1)} people · {(e.traversal_seconds/60).toFixed(1)} min</p><p>{e.closed?'Closed to new entrants':'Open pathway'}</p></Popup></Polyline>})}
 {nodes.map(n=>n.kind==='junction'?<CircleMarker key={n.id} center={[n.y,n.x]} radius={3} pathOptions={{color:'#7f9d8b',weight:1,fillColor:'#fff',fillOpacity:1}}><Tooltip>{n.name}</Tooltip></CircleMarker>:<React.Fragment key={n.id}><Rectangle bounds={[[n.y-12,n.x-15],[n.y+12,n.x+15]]} pathOptions={{color:'#486e5b',weight:1.5,fillColor:'#e4ecde',fillOpacity:1}}/><CircleMarker center={[n.y,n.x]} radius={3} pathOptions={{color:'#245a43',fillOpacity:1}}><Tooltip permanent direction="top" offset={[0,-9]} className="building-label">{n.name}</Tooltip></CircleMarker></React.Fragment>)}
 {state?.pedestrians?.map(p=><CircleMarker key={`p${p.id}`} center={[p.y,p.x]} radius={2.4} pathOptions={{color:p.status==='waiting'?'#d88735':'#204b72',weight:0,fillOpacity:.8}}><Tooltip>Pedestrian {p.id} · {p.status}</Tooltip></CircleMarker>)}
 </MapContainer><div className="map-legend"><span><i style={{background:'#64a889'}}/> Free flowing</span><span><i style={{background:'#dfab49'}}/> Building up</span><span><i style={{background:'#de6452'}}/> Above capacity</span><span><i style={{background:'#7e8791'}}/> Closed</span><span className="ml-auto">Coordinates & distances in metres</span></div></div>
}
