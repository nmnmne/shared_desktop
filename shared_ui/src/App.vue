<template>
  <Header />

  <div class="content">

    <main class="main">
      <router-view />
    </main>
  </div>

  <!-- <Footer /> -->
</template>

<script>
import Header from "@/components/Header.vue";
import SidebarAll from "@/components/SidebarAll.vue";
import SidebarPotok from "@/components/SidebarPotok.vue";
import SidebarSwarco from "@/components/SidebarSwarco.vue";
import SidebarPeek from "@/components/SidebarPeek.vue";
import Footer from "@/components/Footer.vue";

export default {
  name: "App",
  components: {Footer, Header, SidebarAll, SidebarPotok, SidebarSwarco, SidebarPeek},
};
</script>

<style>
#app {
  font-family: Arial, sans-serif;
  color: #d9d9d9;
  background-color: #151515;
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.content {
  display: flex;
  flex: 1;
}

.main {
  flex: 1;
  background: var(--gray-800);
}

.footer {
  background: #212121;
  padding: 10px 20px;
  text-align: center;
  color: #d9d9d9;
}

.footer p {
  margin: 0;
}
</style>
