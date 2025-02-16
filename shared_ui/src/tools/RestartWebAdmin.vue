<template>
  <div>
    <h2>Перезагрузка web интерфейса ДК Поток</h2>

    <form @submit.prevent="handleSubmit" class="form-inline">
        <input
          type="text"
          v-model="ipAddress"
          class="form-control"
          placeholder="IP адрес"
          required
          autocomplete="off"
        />
        <button type="submit">Перезагрузка</button>
    </form>

    <p :style="{ color: responseMessage.color }">{{ responseMessage.text }}</p>
  </div>
</template>

<script>
import { serverIPs } from '@/assets/js/config';

export default {
  name: "RestartWebAdmin",
  data() {
    return {
      ipAddress: '',
      responseMessage: {
        text: '',
        color: 'green',
      },
      serverIPs: serverIPs,
      apiPath: '/api/restart_web_admin/',
    };
  },
  methods: {
    async handleSubmit() {
      for (let ip of this.serverIPs) {
        const server = `http://${ip}${this.apiPath}`;
        
        try {
          const response = await fetch(server, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': this.getCookie('csrftoken'),
            },
            body: JSON.stringify({ ip_address: this.ipAddress }),
          });

          const data = await response.json();

          if (data.status === 'success') {
            this.responseMessage.color = 'green';
            this.responseMessage.text = data.message;
            return;
          } else {
            this.responseMessage.color = 'red';
            this.responseMessage.text = data.message;
            return;
          }
        } catch (error) {
          console.warn(`Ошибка подключения к ${server}:`, error);
        }
      }

      this.responseMessage.color = 'red';
      this.responseMessage.text = 'Ошибка при подключении ко всем серверам.';
    },

    getCookie(name) {
      const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
      if (match) return match[2];
    },
  },
};
</script>


<style scoped>
  input[type="text"]{
    padding: 3px;
    border-radius: 6px;
  
  }
</style>
