<script setup>
/**
 * @description 总数统计
 */
import { getCountAPI } from '@/api/list'
import { ref } from 'vue'

defineOptions({
  inheritAttrs: false,
})
const { configData } = defineProps(['configData'])

const list = ref(configData.list)
list.value.forEach(async item => {
  let res = await getCountAPI(item.tableName)
  item.count = res.data
})
</script>

<template>
  <div class="statis-wrapper" v-if="list.length">
    <div v-for="(item, index) in list" :class="'statis-' + (index + 1)">
      <div class="block"></div>
      <div class="info">
        <div class="title">{{ item.comments }}</div>
        <div class="num">{{ item.count }}</div>
      </div>
    </div>
  </div>
</template>
