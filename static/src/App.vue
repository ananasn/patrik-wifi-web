<template>
  <div id="app">

    <div class="flex-container">
      <select v-model="ssid" class="custom-select">
        <option value="" disabled selected hidden>Выберите сеть</option>
        <option 
          v-for="option in options"
          v-bind:key="option.value"
          :value="option.text"
        >
          {{ option.text }}
        </option>
      </select>

      <button @click="loadSSID">Обновить</button>
    </div>

    <div class="flex-container">
      <input
        :value="input"
        class="input master-flex"
        @input="onInputChange"
        :type="passwordFieldType"
        placeholder="Введите пароль от Wi-Fi сети"
      >

      <button class="slave-flex" type="password" @click="switchVisibility">Показать пароль</button>
    </div>

    <SimpleKeyboard 
      @onChange="onChange" 
      @onKeyPress="onKeyPress" 
      :input="input"
    />

    <div class="alert"> {{ message }} </div>
  </div>
</template>

<script>
import axios from "axios"

import SimpleKeyboard from "./SimpleKeyboard"
import "./App.css"

export default {
  name: "App",
  components: {
    SimpleKeyboard
  },
  data: () => ({
    input: "",
    ssid: "",
    message: "",
    options: [],
    passwordFieldType: "password"

  }),
  mounted: function() {
    this.loadSSID();
  },
  methods: {
    connect(ssid, password) {
      axios.post("http://localhost:8888/connect/", { 
        ssid: ssid, 
        password: password
      })
      .then(response => {
        this.message = response.data.message 
        console.log(response.data)
      })
      .catch(error => {
        console.log(error)
      })
    },
    loadSSID() {
      this.message = "Обновляется список сетей, подождите..."
      axios.get("http://localhost:8888/ssid/")
      .then(response => {
        this.options = response.data
        this.message = ""
      })
      .catch(error => {
        console.error(error)
      })
    },
    onChange(input) {
      this.input = input
    },
    onKeyPress(button) {
      if (button === "{enter}"){
        if (this.ssid && this.input) {
          this.connect(this.ssid, this.input)
          this.message = ""
        } else {
          this.message = "Не выбрана сеть и/или не введён пароль"
        }
      }
    },
    onInputChange(input) {
      this.input = input.target.value
    },
    switchVisibility() {
      this.passwordFieldType = this.passwordFieldType === "password" ? "text" : "password";
    }
  }
};
</script>
