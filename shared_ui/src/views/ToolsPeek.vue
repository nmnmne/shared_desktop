<template>
  <div class="tools-page">
    <SidebarPeek :toolsData="toolsData" @change-tool="handleChangeTool" />
    <div class="tools">
      <div v-if="!currentTool">Выберите инструмент</div>
      <div v-else>
        <PeekProcesses v-if="currentTool.toolName === 'PeekProcesses'" />
      </div>

    </div>
  </div>
</template>

<script setup>
import SidebarPeek from "@/components/SidebarPeek.vue";
import {onMounted, ref} from "vue";
import PeekProcesses from "@/tools/PeekProcesses.vue";

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
