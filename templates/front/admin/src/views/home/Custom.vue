<template>
  <el-calendar v-model="value" />
</template>

<script setup>
import { ref } from 'vue'

const value = ref(new Date())
</script>

<style>
.el-calendar{
    border-radius:10px;
}
</style>