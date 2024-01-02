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

      <button @click="loadSSID">⟳</button>
    </div>

    <input
      :value="input"
      class="input"
      @input="onInputChange"
      type="password"
      placeholder="Введите пароль от Wi-Fi сети"
    >
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
    options: []

  }),
  mounted: function() {
    this.loadSSID();
  },
  methods: {
    connect: function(ssid, password) {
      axios.post("http://localhost:8888/connect/", { 
        ssid: ssid, 
        password: password
      })
      .then(response => {
        this.message = response.data.ssid
        console.log(response)
      })
      .catch(error => {
        console.log(error)
      })
    },
    loadSSID: function() {
      axios.get("http://localhost:8888/ssid/")
      .then(response => {
        this.options = response.data
        console.log(response.data)
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
    }
  }
};
</script>
