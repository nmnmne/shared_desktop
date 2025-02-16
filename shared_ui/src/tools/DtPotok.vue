<template>
  <div>
    <h2>Генерация строки для программирования ДК Поток</h2>

    <!-- Форма для ввода -->
    <div>
      <input 
        type="text" 
        v-model="detRangesAndGroup" 
        placeholder="Пример: 1-4, 7-12, 3" 
        class="form-control" 
      />
      <button @click="generateCondition" class="btn btn-primary mt-2">
        Сгенерировать
      </button>
    </div>

    <!-- Поле для вывода результата -->
    <div v-if="response">
      <h4>Результат:</h4>
      <textarea class="form-control" rows="4" readonly>{{ response }}</textarea>
    </div>

    <!-- Поле для вывода ошибки -->
    <div v-if="error" class="alert alert-danger mt-3">
      <strong>Ошибка:</strong> {{ error }}
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { serverIPs } from '@/assets/js/config';

export default {
  name: "DtPotok",
  data() {
    return {
      detRangesAndGroup: "",
      response: null,
      error: null,
      servers: serverIPs.map(ip => `http://${ip}/tools/dt_potok_api/`),
    };
  },
  methods: {
    async generateCondition() {
      this.error = null;
      this.response = null;

      for (let server of this.servers) {
        try {
          const res = await axios.post(server, {
            det_ranges_and_group: this.detRangesAndGroup,
          });

          if (res.data.condition_string) {
            this.response = res.data.condition_string;
            return;
          } else if (res.data.error) {
            this.error = res.data.error;
            return;
          }
        } catch (err) {
          console.warn(`Ошибка подключения к ${server}:`, err);
        }
      }

      this.error = "Ошибка при подключении к серверам.";
    },
  },
};
</script>

<style scoped>
  input[type="text"]{
    padding: 7px;
    border-radius: 6px;
  
  }
</style>
