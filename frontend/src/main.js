import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import {Tabs, Tab} from 'vue3-tabs-component';
import VueAwesomePaginate from "vue-awesome-paginate";

import './assets/main.css'
import "vue-awesome-paginate/dist/style.css";

const app = createApp(App).component('tabs', Tabs).component('tab', Tab);
app.use(VueAwesomePaginate)
app.use(router)

app.mount('#app')
