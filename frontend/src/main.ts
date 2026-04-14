import { createApp } from "vue";
import ElementPlus from "element-plus";
import * as ElementPlusIconsVue from "@element-plus/icons-vue";
import "element-plus/dist/index.css";

import App from "./App.vue";
import { router } from "./router";
import { pinia } from "./stores";
import { permissionDirective } from "./directives/permission";
import "./styles/global.scss";

const app = createApp(App);

Object.entries(ElementPlusIconsVue).forEach(([key, component]) => {
  app.component(key, component);
});

app.use(pinia);
app.use(router);
app.use(ElementPlus);
app.directive("permission", permissionDirective);

app.mount("#app");
