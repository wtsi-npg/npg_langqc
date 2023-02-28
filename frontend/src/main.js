import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import * as ElementPlusIconsVue from '@element-plus/icons-vue';

import './assets/main.css'

const app = createApp(App);
const pinia = createPinia();

app.use(router);
app.use(ElementPlus); // Configure global element options here
app.component('Link', ElementPlusIconsVue.Link);
app.use(pinia);

app.mount('#app');
