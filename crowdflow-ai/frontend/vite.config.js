import {defineConfig} from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({plugins:[react()],build:{rollupOptions:{output:{manualChunks:{charts:['recharts'],map:['leaflet','react-leaflet']}}}},server:{proxy:Object.fromEntries(['/graph','/locations','/scenarios','/predict','/route','/simulate','/simulation','/analytics','/model','/compare','/benchmarks','/health'].map(x=>[x,'http://127.0.0.1:8000']))},test:{environment:'jsdom',setupFiles:['./src/test-setup.js'],include:['src/**/*.test.jsx']}})
