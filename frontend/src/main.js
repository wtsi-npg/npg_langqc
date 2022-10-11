import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import {Tabs, Tab} from 'vue3-tabs-component';

import './assets/main.css'

const app = createApp(App).component('tabs', Tabs).component('tab', Tab);

app.use(router)

app.mount('#app')
