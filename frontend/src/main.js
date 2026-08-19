// 前端入口：创建 Vue 应用，统一挂载路由和全局样式。
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './style.css'

createApp(App).use(router).mount('#app')
