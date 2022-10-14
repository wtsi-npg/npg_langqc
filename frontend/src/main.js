import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import {Tabs, Tab} from 'vue3-tabs-component';
import VPagination from "@hennge/vue3-pagination";
import "@hennge/vue3-pagination/dist/vue3-pagination.css";

import './assets/main.css'

const app = createApp(App).component('tabs', Tabs).component('tab', Tab);

app.component('VPagination', VPagination);
app.use(router);

app.mount('#app');
