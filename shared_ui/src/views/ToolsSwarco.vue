<template>
    <div class="tools-page">
      <SidebarSwarco :toolsData="toolsData" @change-tool="handleChangeTool" />
      <div class="tools">
        <div v-if="!currentTool">Выберите инструмент</div>
        <div v-else>

        </div>

      </div>
    </div>
  </template>
  
  <script setup>
  import SidebarSwarco from "@/components/SidebarSwarco.vue";
  import {onMounted, ref} from "vue";
  // import Tool1 from "@/tools/Tool1.vue";

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
  