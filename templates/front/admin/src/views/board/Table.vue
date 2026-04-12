<script setup>
import { getPageAPI } from '@/api/list'
import TableImage from '@/components/TableItem/components/TableImage.vue'
import { onUnmounted, ref } from 'vue'
import tableConfigs from '@/utils/tableConfigs'
/**
 * @description 表格
 */

const { configData, animation } = defineProps(['configData', 'animation'])
let { chartSort, title, tableName, imgKey, imgTitle, textNames } = configData
let sortColumn = tableConfigs[tableName].columns.find(
  column => column.sort == '升' || column.sort == '降'
)
if (sortColumn) {
  title = title + '(' + sortColumn.comments + 'TOP20)'
}
// 拉取后端数据
const list = ref([])
const fetchData = async () => {
  let apiParams = {
    page: 1,
    limit: 20,
    _t: Date.now(),
  }
  if (sortColumn) {
    apiParams.order = sortColumn.sort == '升' ? 'asc' : 'desc'
    apiParams.sort = sortColumn.columnName
  }
  let res = await getPageAPI(tableName, apiParams)
  list.value = res.data.list

  if (list.value.length) {
    startScroll()
  }
}
fetchData()

// 斑马纹
const tableRowClassName = ({ row, rowIndex }) => {
  return rowIndex % 2 === 0 ? 'even-row' : 'odd-row'
}

// ----------------------------------
// ---------- 滚动事件 ---------------
// ----------------------------------
let timer = null
let scrollBox = null
let rowHeight = 62
let startScroll = () => {
  if (!animation.flag) {
    return
  }

  timer && clearInterval(timer)
  timer = setInterval(scrollEvent, animation.time)
}

let stopScroll = () => {
  timer && clearInterval(timer)
  timer = null
}
let scrollEvent = () => {
  if (!scrollBox) {
    scrollBox = document.querySelector('.el-scrollbar__wrap')
    rowHeight = document.querySelector('.el-table__row').clientHeight
  }

  if (scrollBox) {
    let top = 0
    if (scrollBox.scrollHeight - scrollBox.scrollTop === scrollBox.clientHeight) {
      // 滚动条到底了，返回最顶层
      top = 0
    } else {
      // 向下滚动rowHeight的距离
      top = scrollBox.scrollTop + rowHeight
    }

    scrollBox.scrollTo({
      top,
      behavior: 'smooth',
    })
  }
}
onUnmounted(() => {
  stopScroll()
})
</script>

<template>
  <div :class="'char-wrapper-' + chartSort">
    <div class="title">
      <div class="text">{{ title }}</div>
    </div>

    <div class="chart-wrapper" @mouseenter="stopScroll" @mouseleave="startScroll">
      <el-table :data="list" :row-class-name="tableRowClassName">
        <el-table-column
          v-for="item in textNames"
          :key="item.key"
          :prop="item.key"
          :label="item.title"
        />
        <el-table-column :prop="imgKey" :label="imgTitle" v-if="imgKey">
          <template #default="scope">
            <TableImage :value="scope.row[imgKey]" />
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>
