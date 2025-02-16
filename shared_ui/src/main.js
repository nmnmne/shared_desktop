import { createApp } from "vue";
import "./assets/css/main.css";
import App from "./App.vue";
import router from "./router";
import Vueform from '@vueform/vueform'
import vueformConfig from './../vueform.config'

const app = createApp(App);
app.use(router);
app.use(Vueform, vueformConfig)
app.mount("#app");
