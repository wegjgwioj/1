<script setup>
import { getFilePaths } from '@/utils/getFilePath'
import base from '@/utils/base'
import { computed } from 'vue'

/**
 * @description 图片
 */
defineOptions({
  inheritAttrs: false,
})
const { value, tableName } = defineProps(['value', 'tableName'])

let srcList = computed(() => {
  if (tableName == 'qrcode') {
    return [base.get().url + 'qrcode?content=' + value]
  }
  return getFilePaths(value)
})
</script>

<template>
  <el-image
    class="table-image"
    preview-teleported
    :src="srcList[0] || ''"
    :preview-src-list="srcList"
    show-progress
    fit="cover"
  >
    <template #error>
      <div class="table-image-placeholder">暂无图片</div>
    </template>
  </el-image>
</template>

<style scoped>
.table-image-placeholder {
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eef3f8;
  color: #8b95a7;
  font-size: 12px;
  border-radius: 8px;
}
</style>
