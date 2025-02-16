<template>
  <div class="header">
    <div class="brand">
      <img src="@/assets/img/logo.png" width="22" height="22" alt="Logo" />
      <span>Рабочий стол транспортного инженера</span>
    </div>
    <nav>
      <ul class="nav-list nav-list_right">
        <li v-for="item in menu" :key="item.id">
          <router-link
            :to="item.path"
            :class="{ active: route.path === item.path }"
          >
            {{ item.title }}
          </router-link>
        </li>
      </ul>
    </nav>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();

const menu = ref([
  {
    id: 1,
    title: "Главная",
    path: "/",
  },
  {
    id: 2,
    title: "Поток",
    path: "/tools_potok",
  },
  {
    id: 3,
    title: "Swarco",
    path: "/tools_swarco",
  },
  {
    id: 4,
    title: "Peek",
    path: "/tools_peek",
  },
  {
    id: 5,
    title: "Общее",
    path: "/tools_all",
  },
]);
</script>

<style lang="scss" scoped>

* {
  white-space: nowrap; /* Запрещаем перенос на новую строку для всех элементов */
}
.header {
  background: var(--gray-960);
  padding: 4px 15px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  display: flex;
  align-items: center;
}

.brand img {
  margin-right: 4px; 
}

.brand span {
  margin-top: 2px;
}

.nav-list {
  list-style: none;
  display: flex;
  margin: 0;
  padding: 1px 10px;
  margin-top: 2px;
  gap: 20px;

  li {
    display: inline;
  }

  a {
    text-decoration: none;
    color: #d9d9d9;
    padding: 0px 1px;
    border-radius: 3px;
    transition: background-color 0.2s ease;
    position: relative
  }

  &_right {
    margin-left: auto;
  }

  li:hover a {
    background-color: var(--blue1);
    color: rgb(232, 232, 232);
  }

  a.active {
    background-color: var(--gray-700);
  }

  li a::after {
  content: "";
  position: absolute;
  left: 50%;
  bottom: -4px;
  width: 0;
  height: 3px;
  background-color: var(--gray-400);
  border-radius: 1px;
  transition: width 0.3s ease, left 0.3s ease;
}

  a.active::after {
    width: 100%;
    left: 0;
  }
}

@media (max-width: 700px) {
  .brand span {
    display: none; /* Скрываем блок .brand на экранах менее 400px */
  }
}
</style>
