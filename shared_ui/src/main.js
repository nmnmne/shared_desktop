import { createApp } from "vue";
import "@/assets/css/Main.scss";
import "@/assets/css/Theme.scss";
import '@/assets/fonts/fonts.css';
import App from "./App.vue";
import router from "./router";
import Vueform from '@vueform/vueform';
import vueformConfig from './../vueform.config';
import axios from 'axios';

const app = createApp(App);
// console.log('API Token in main.js:', import.meta.env.VITE_API_TOKEN);
// Добавляем axios в глобальные свойства
app.config.globalProperties.$axios = axios;

// Используем router и Vueform
app.use(router);
app.use(Vueform, vueformConfig);

// Монтируем приложение
app.mount("#app");