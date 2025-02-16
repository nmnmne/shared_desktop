import { createRouter, createWebHistory } from 'vue-router';

import home from '../views/Home.vue';
import tools_all from '../views/ToolsAll.vue';
import tools_potok from '../views/ToolsPotok.vue';
import tools_swarco from '../views/ToolsSwarco.vue';
import tools_peek from '../views/ToolsPeek.vue';

const routes = [
  { path: '/', component: home  },
  { path: '/tools_all', component: tools_all  },
  { path: '/tools_potok', component: tools_potok  },
  { path: '/tools_swarco', component: tools_swarco  },
  { path: '/tools_peek', component: tools_peek  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
