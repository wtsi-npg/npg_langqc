import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';

import {Tabs, Tab} from 'vue3-tabs-component';

import './assets/main.css'

const app = createApp(App).component('tabs', Tabs).component('tab', Tab);

app.use(router);
app.use(ElementPlus); // Configure global element options here

app.mount('#app');
