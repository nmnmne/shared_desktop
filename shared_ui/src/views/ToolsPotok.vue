<template>
  <div class="tools-page">
    <SidebarPotok :toolsData="toolsData" @change-tool="handleChangeTool" />
    <div class="tools">
      <div v-if="!currentTool">Выберите инструмент</div>
      <div v-else>
        <RestartWebAdmin v-if="currentTool.toolName === 'RestartWebAdmin'" />
        <DtPotok v-if="currentTool.toolName === 'DtPotok'" />
      </div>

    </div>
  </div>
</template>

<script setup>
import SidebarPotok from "@/components/SidebarPotok.vue";
import {onMounted, ref} from "vue";
import RestartWebAdmin from "@/tools/RestartWebAdmin.vue";
import DtPotok from "@/tools/DtPotok.vue";

const currentTool = ref(null);

const handleChangeTool = (tool) => {
  currentTool.value = tool;
}

</script>

<style scoped>
.tools {
  padding: 20px;
  flex-grow: 1;
}

.tools-page {
  display: flex;
  height: 100%;
}

</style>
  