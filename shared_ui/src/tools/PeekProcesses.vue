<template>
  <div>
    <h2 style="margin-bottom: 20px">Расчет процессов Peek</h2>
    <label for="processCount">Выберите количество процессов: </label>
    <select v-model="selectedProcessCount" id="processCount">
      <option v-for="n in 4" :key="n" :value="n">{{ n }}</option>
    </select>
    <div class="list-button">
      <div v-for="i in selectedProcessCount" :key="i" class="tool-form">
        <input 
          type="text" 
          :name="'title' + i" 
          :placeholder="'Процесс ' + i" 
          v-model="processes[i - 1].title"
          autocomplete="off"
        >
        <textarea 
          :name="'value' + i" 
          rows="6" 
          v-model="processes[i - 1].value"
          autocomplete="off"
        ></textarea>
      </div>
    </div>
    <pre class="hidden">{{ transformedProcesses }}</pre>
    <button @click="sendData">Рассчитать</button>

    <!-- Модальное окно с ответом -->
    <div v-if="showModal" class="modal">
      <div class="modal-content">
        <span class="close" @click="showModal = false">&times;</span>
        <div v-for="i in selectedProcessCount" :key="i" class="modal-output">
          <label>{{ 'Процесс ' + i }}</label>
          <input type="text" :value="responseData[i]?.[0] || ''" readonly>
          <textarea rows="4" :value="responseData[i]?.[1].join('\n') || ''" readonly></textarea>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { serverIPs } from '@/assets/js/config';

export default {
  name: "PeekProcessess",
  data() {
    return {
      selectedProcessCount: 2,
      processes: Array.from({ length: 4 }, () => ({ title: '', value: '' })),
      responseData: {},
      responseMessage: '',
      responseIsError: false,
      showModal: false,
      serverIPs: serverIPs,
      apiPath: "/api/v1/peek-processes/",
    };
  },
  computed: {
    transformedProcesses() {
      const result = {};
      this.processes.forEach((process, index) => {
        if (index < this.selectedProcessCount) {
          const processNumber = index + 1;
          const values = process.value.split('\n').map(val => val.trim());
          result[processNumber] = [process.title, values.length > 1 ? values : [values[0]]];
        }
      });
      return result;
    }
  },
  methods: {
    async sendData() {
      for (let ip of this.serverIPs) {
        let server = `http://${ip}${this.apiPath}`;

        try {
          const response = await axios.post(server, this.transformedProcesses);
          this.responseData = response.data.repaired_cmd_sg;
          this.responseIsError = false;
          this.showModal = true;
          return;
        } catch (error) {
          console.warn(`Ошибка подключения к ${server}:`, error);
        }
      }

      // Если ни один сервер не ответил
      this.responseMessage = "Ошибка при отправке данных ко всем серверам.";
      this.responseIsError = true;
      this.showModal = true;
    }
  }
};
</script>

<style scoped>

</style>
