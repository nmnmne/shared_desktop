import { createApp } from "vue";
import "./assets/css/Main.scss";
import App from "./App.vue";
import router from "./router";
import Vueform from '@vueform/vueform';
import vueformConfig from './../vueform.config';
import axios from 'axios';

const app = createApp(App);
console.log('API Token in main.js:', import.meta.env.VUE_APP_API_TOKEN);

// Добавляем axios в глобальные свойства
app.config.globalProperties.$axios = axios;

// Определяем тему и динамически импортируем SCSS
const savedTheme = localStorage.getItem('theme') === 'true' ? 'Dark' : 'Light';
import(`./assets/css/${savedTheme}.scss`)
  .then(() => console.log(`${savedTheme}.scss загружен`))
  .catch(err => console.error("Ошибка загрузки темы:", err));

// Используем router и Vueform
app.use(router);
app.use(Vueform, vueformConfig);

// Монтируем приложение
app.mount("#app");
