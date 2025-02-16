<template>
    <div class="tools-page">
      <SidebarAll :toolsData="toolsData" @change-tool="handleChangeTool" />
      <div class="tools">
        <div v-if="!currentTool">Выберите инструмент</div>
        <div v-else>
          <ApiDir v-if="currentTool.toolName === 'ApiDir'" />
          <!-- <Tool2 v-if="currentTool.toolName === 'tool2'" /> -->
        </div>

      </div>
    </div>
  </template>
  
  <script setup>
  import SidebarAll from "@/components/SidebarAll.vue";
  import {onMounted, ref} from "vue";
  import ApiDir from "@/tools/ApiDir.vue";

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
  