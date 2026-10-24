import '@testing-library/jest-dom/vitest'
import {vi,beforeEach,afterEach} from 'vitest'
import {cleanup} from '@testing-library/react'
const nativeFetch=globalThis.fetch
vi.stubGlobal('fetch',(path,opts)=>nativeFetch(new URL(path,'http://127.0.0.1:8000').href,opts))
Object.defineProperty(HTMLElement.prototype,'clientWidth',{configurable:true,get(){return 720}})
Object.defineProperty(HTMLElement.prototype,'clientHeight',{configurable:true,get(){return 450}})
HTMLElement.prototype.getBoundingClientRect=function(){return {x:0,y:0,top:0,left:0,right:720,bottom:450,width:720,height:450,toJSON(){}}}
SVGSVGElement.prototype.createSVGRect=()=>({})
vi.stubGlobal('ResizeObserver',class{constructor(callback){this.callback=callback}observe(target){this.callback([{target,contentRect:{width:720,height:450}}])}unobserve(){}disconnect(){}})
window.matchMedia=()=>({matches:false,addListener(){},removeListener(){},addEventListener(){},removeEventListener(){}})
afterEach(()=>cleanup())
beforeEach(async()=>{await nativeFetch('http://127.0.0.1:8000/simulate/reset',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})})
