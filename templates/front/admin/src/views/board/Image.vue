<script setup>
/**
 * @description 图文
 */
import { getPageAPI } from '@/api/list'
import { getFirstFilePath } from '@/utils/getFilePath'
import { ref, onUnmounted } from 'vue'
import tableConfigs from '@/utils/tableConfigs'

const { configData, animation } = defineProps(['configData', 'animation'])
let { chartSort, title, tableName, imgKey, textNames } = configData
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
  }
  if (sortColumn) {
    apiParams.order = sortColumn.sort == '升' ? 'asc' : 'desc'
    apiParams.sort = sortColumn.columnName
  }
    let res = await getPageAPI(tableName, apiParams)

  // 处理图片路径
  if (imgKey) {
    res.data.list.forEach(item => {
      item[imgKey] = getFirstFilePath(item[imgKey])
    })
  }

  list.value = res.data.list

  if (list.value.length) {
    startScroll()
  }
}
fetchData()

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
    scrollBox = document.querySelector('.img-wrapper')
    rowHeight = document.querySelector('.img-wrapper .item').clientHeight
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

    <div class="img-wrapper" @mouseenter="stopScroll" @mouseleave="startScroll">
      <div class="item" v-for="item in list" :key="item.id">
        <img class="img" :src="item[imgKey]" draggable="false" />

        <div v-for="(i, index) in textNames" :key="i.key" :class="'title' + (index + 1)">
          {{ item[i.key] }}
        </div>
      </div>
    </div>
  </div>
</template>
