export async function api(path,body){
 const response=await fetch(path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
 const result=await response.json()
 if(!response.ok)throw new Error(typeof result.detail==='string'?result.detail:JSON.stringify(result.detail||result))
 return result
}
export const formatTime = value => value==null?'—':`${(value/60).toFixed(1)} min`
export const clock = minute => `${String(Math.floor(minute/60)%24).padStart(2,'0')}:${String(Math.floor(minute%60)).padStart(2,'0')}`
export const minuteValue = time => {const [h,m]=time.split(':').map(Number);return h*60+m}
export const strategyNames={distance:'Distance-only Dijkstra',congestion:'Congestion-aware Dijkstra',adaptive:'CrowdFlow adaptive',astar:'A* predicted-time'}
