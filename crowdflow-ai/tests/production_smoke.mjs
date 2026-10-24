// Execute the delivered production ESM bundle in jsdom, using the live API.
import {JSDOM} from '../frontend/node_modules/jsdom/lib/api.js'
import {readFile} from 'node:fs/promises'
import {pathToFileURL} from 'node:url'
import {resolve} from 'node:path'
const root=resolve(import.meta.dirname,'..')
const html=await readFile(resolve(root,'frontend/dist/index.html'),'utf8')
const dom=new JSDOM(html,{url:'http://127.0.0.1:8000/',pretendToBeVisual:true})
const {window}=dom
for(const key of ['window','document','navigator','HTMLElement','Element','SVGElement','SVGSVGElement','getComputedStyle','MutationObserver','Event','MouseEvent','requestAnimationFrame','cancelAnimationFrame']){
 const value=window[key];Object.defineProperty(globalThis,key,{value:typeof value==='function'&&['getComputedStyle','requestAnimationFrame','cancelAnimationFrame'].includes(key)?value.bind(window):value,configurable:true,writable:true})
}
Object.defineProperty(window.HTMLElement.prototype,'clientWidth',{get:()=>720})
Object.defineProperty(window.HTMLElement.prototype,'clientHeight',{get:()=>450})
window.HTMLElement.prototype.getBoundingClientRect=()=>({x:0,y:0,top:0,left:0,right:720,bottom:450,width:720,height:450})
window.SVGSVGElement.prototype.createSVGRect=()=>({})
globalThis.ResizeObserver=class{constructor(cb){this.cb=cb}observe(target){this.cb([{target,contentRect:{width:720,height:450}}])}disconnect(){}unobserve(){}}
window.ResizeObserver=globalThis.ResizeObserver
const realFetch=globalThis.fetch
globalThis.fetch=(url,options)=>realFetch(new URL(url,'http://127.0.0.1:8000').href,options)
const errors=[]
window.addEventListener('error',e=>errors.push(e.message))
const entry=html.match(/src="(\/assets\/[^\"]+\.js)"/)[1]
await import(pathToFileURL(resolve(root,'frontend/dist'+entry)))
async function until(fn){const end=Date.now()+10000;while(Date.now()<end){if(fn())return;await new Promise(r=>setTimeout(r,50))}throw new Error('Production DOM did not reach expected state')}
await until(()=>document.querySelector('select[aria-label="From"]')?.options.length===36)
await until(()=>document.querySelectorAll('.leaflet-overlay-pane path').length>66)
const buttons=()=>[...document.querySelectorAll('button')]
buttons().find(b=>b.textContent==='Calculate route').click()
await until(()=>document.querySelector('[data-testid="route-result"]')?.textContent.includes('500 pedestrians'))
buttons().find(b=>b.textContent==='ML intelligence').click()
await until(()=>document.querySelectorAll('.recharts-line-curve').length===2)
buttons().find(b=>b.textContent==='Experiments').click()
await until(()=>document.querySelectorAll('tbody tr').length===3)
buttons().find(b=>b.textContent==='Live simulation').click()
await until(()=>document.querySelector('.leaflet-container'))
if(errors.length)throw new Error(errors.join('\n'))
console.log('Production bundle smoke passed: graph, route, analytics, experiments, live simulation.')
window.close();process.exit(0)
