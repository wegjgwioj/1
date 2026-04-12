<script setup>
import '@/style/list.scss'
import '@/components/TableItem/index'

import { onMounted, reactive, ref, watch, watchEffect, shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ListSearch from './ListSearch.vue'
import ListView from './ListView.vue'
import ListEdit from './ListEdit.vue'
import CommonInfo from './components/CommonInfo.vue'
import UploadXlsx from './components/UploadXlsx.vue'
import ChartEntry from '@/components/Echart/index.vue'
import { 
  getPageAPI, 
  getAutoSort2API,
  deleteAPI, 
  updateAPI, 
  spiderAPI, 
  predictAPI, 
  predictImgAPI,
  cleanseAPI,
  addAPI,
  getDetailAPI,
  getListAPI,
  toggleStoreupAPI,
  crawlVehicleKnowledgeAPI,
  crawlVehicleKnowledgeBatchAPI,
} from '@/api/list'
import { 
  getGroupAPI, 
  deleteExamrecordAPI,
  getRemindAPI,
  commonTableAPI,
} from '@/api/common'
import { getColums } from '@/utils/form'
import { getHeaderButtons, getTableButtons } from '@/utils/getListButtons'
import { loop } from '@/utils/auth'
import tableConfigs from '@/utils/tableConfigs'
import dayjs from 'dayjs'
import { utils, writeFileXLSX } from 'xlsx'
import chartData from '@/components/Echart/chartData'
import { getAvatar, downloadFile } from '@/utils'
import getFilePath from '@/utils/getFilePath'

/**
 * @description 列表页面
 */
const route = useRoute()
const router = useRouter()

// 表名
let tableName = route.path.split('/')[1]
let { table } = tableConfigs[tableName]

// 所有列
let columns = getColums(tableName, 'list', { configType: route.params.type })

// 列表数据和加载
const datas = ref([])
const isLoading = ref(false)

// ----------------------------------
// ---------- 排序配置 ---------------
// ----------------------------------
const sortData = ref(
  table.sortName
    ? {
        sort: table.sortName,
        order: table.sortOrder,
      }
    : {}
)
const defaultSort = table.sortName
  ? {
      prop: table.sortName,
      order: table.sortOrder == 'asc' ? 'ascending' : 'descending',
    }
  : {}
function sortChangeEvent(data) {
  let { order, prop } = data
  switch (order) {
    case 'descending':
      sortData.value = {
        sort: prop,
        order: 'desc',
      }
      break
    case 'ascending':
      sortData.value = {
        sort: prop,
        order: 'asc',
      }
      break

    default:
      sortData.value = {}
      break
  }
}

// ----------------------------------
// ---------- 搜索配置 ---------------
// ----------------------------------
const searchData = ref({})
const searchEvent = data => {
  searchData.value = data
}

// ----------------------------------
// ---------- 分页配置 ---------------
// ----------------------------------
const pageSizes = [1, 2, 3, 4, 5, 10].map(base => 10 * base)
const layout = ["total","sizes","prev","pager","next"].join(',')
const currentPage = ref(1)
const pageSize = ref(pageSizes[0])
const total = ref(100)

// ----------------------------------
// ---------- 多选框 ---------------
// ----------------------------------
const selectedDatas = ref([])
const selectionChange = val => {
  selectedDatas.value = val
}

// ----------------------------------
// ---------- 弹框公共 ---------------
// ----------------------------------
const dialogVisible = ref(false)
const dialogTitle = ref('弹框标题')
const dialogComponent = shallowRef(null)
const dialogClass = ref('')
let dialogData = {}
function openDialog(data) {
  data.dialogTitle && (dialogTitle.value = data.dialogTitle)
  
  dialogComponent.value = data.dialogComponent
  dialogData = data.dialogData
  dialogClass.value = data.dialogClass

  dialogVisible.value = true
}

// ----------------------------------
// ---------- 操作按钮 ---------------
// ----------------------------------
const menuTableName = route.path.replace(/^\//, '')
const tableButtons = getTableButtons(tableName, menuTableName)
const listMode = ref('page')
// 部分按钮，特殊条件下不显示
function getShow_tableButtons(button, row) {
  let isShow = true

  if (button.key === 'discussReply') {
    return localStorage.getItem('sessionTable') === 'users'
  }

  if (tableName == 'orders') {
    switch (button.name) {


      default:
        break
    }
  }

  return isShow
}
const actionEventMap = {
  view,
  remove,
  edit,
  messagesReply: edit,
  discuss,
  discussReply,
  storeUp,
  crawlVehicleKnowledge,
  forecast,
}
const actionEvent = (button, row) => {
  let { key, type, title } = button

  // [1] 优先判断是否 跨表功能的按钮
  if (type === 'crossTable') {
    return crossTableHander(button, row)
  }

  // [2] 根据key执行对应方法
  if (actionEventMap[key]) {
    return actionEventMap[key](button, row)
  }

  ElMessage.info(`【${title}】该功能暂时未添加`)
}
// 查看评论
function discuss(button, row) {
  if (tableName === 'drivinglog' && localStorage.getItem('sessionTable') !== 'users') {
    dialogTitle.value = '提交评论'
    dialogComponent.value = ListEdit
    dialogClass.value = ''
    dialogData = {
      type: 'add',
      id: '',
      tableName: 'discussdrivinglog',
      defaultData: {
        refid: row.id,
      },
      okText: '提交',
      cancleText: '取消',
    }
    dialogVisible.value = true
    return
  }
  router.push({ path: `/discuss${tableName}`, query: { refid: row.id } })
}
async function storeUp(button, row) {
  let res = await toggleStoreupAPI({
    refid: row.id,
    tablename: tableName,
  })
  let isStoreup = res.data?.storeup
  ElMessage.success(isStoreup ? '收藏成功' : '已取消收藏')
  fetchData()
}
async function crawlVehicleKnowledge(button, row) {
  let vehiclemodel = row.vehiclemodel
  if (!vehiclemodel) {
    ElMessage.warning('当前记录缺少车型名称，无法采集')
    return
  }
  try {
    let res = await crawlVehicleKnowledgeAPI({ vehiclemodel })
    let status = res.data?.crawlstatus || '成功'
    ElMessage.success(`车型知识采集完成：${vehiclemodel}（${status}）`)
    if (tableName === 'vehicleknowledge') {
      fetchData()
    }
  } catch (error) {
    ElMessage.error(error.msg || error.message || '车型知识采集失败')
  }
}
// 回复评论
function discussReply(button, row) {
  discussReply_vut(button, row)
  return
  dialogTitle.value = button.title
  dialogClass.value = ''
  dialogComponent.value = ListEdit
  dialogData = {
    type: 'update',
    id: row.id,
    tableName,
    row,
    okText: '提交',
    cancleText: '取消',
    isMessageReply: true,
  }
  dialogVisible.value = true
}
function discussReply_vut(button, row) {
  ElMessageBox.prompt('请输入回复内容', '回复: ' + row.nickname, {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    inputPattern: /.+/,
    inputErrorMessage: '请输入回复内容',
    inputType: 'textarea',
  })
    .then(({ value }) => {
      replyEvent(row.id, value)
    })
    .catch(() => {})
}
async function replyEvent(id, content) {
  let { data } = await getDetailAPI(tableName, id)
  let { reply } = data
  let replyData = {
    id: Date.now(),
    userid: Number(localStorage.getItem('userid')),
    avatarurl: localStorage.getItem('useravatar'),
    nickname: localStorage.getItem('username'),
    content,
    addtime: dayjs().format('YYYY-MM-DD HH:mm:ss'),
  }

  // reply是JSON字符串，解析为对象
  let replyList = []
  try {
    replyList = JSON.parse(reply) || []
  } catch (error) {}

  replyList.push(replyData)
  data.reply = JSON.stringify(replyList)

  await updateAPI(tableName, data)
  ElMessage.success('操作成功')
  fetchData()
}

// ----------------------------------
// ---------- 表头按钮 ---------------
// ----------------------------------
const headerButtons = getHeaderButtons(tableName, menuTableName)
const headerEventMap = {
  removes,
  add,
  exportExcel,
  importExcel,
  uploadTemplate,
  downloadTemplate,
  forecast2,
  forecastChart,
  forecastWorkspace,
  dataClean,
  recommend,
  crawlVehicleKnowledgeBatch,
}
function forecastWorkspace() {
  router.push('/forecastWorkbench')
}
const headerEvent = button => {
  let { title, key, type } = button


  if (type === 'statis') {
    // 其它表的统计
    return showChart(button)
  }

  // 根据key执行对应的key事件
  if (headerEventMap[key]) {
    return headerEventMap[key](button)
  }

  ElMessage.info(`【${title}】该功能暂时未添加`)
}
function recommend() {
  listMode.value = listMode.value === 'recommend' ? 'page' : 'recommend'
  currentPage.value = 1
  ElMessage.success(listMode.value === 'recommend' ? '已切换到偏好推荐' : '已切换到默认列表')
  fetchData()
}
async function crawlVehicleKnowledgeBatch() {
  try {
    let res = await crawlVehicleKnowledgeBatchAPI()
    let data = res.data || {}
    ElMessage.success(`批量采集完成：成功 ${data.success || 0} 条，失败 ${data.failed || 0} 条`)
    fetchData()
  } catch (error) {
    ElMessage.error(error.msg || error.message || '批量采集失败')
  }
}

// ----------------------------------
// ---------- 删除功能 ---------------
// ----------------------------------
// 删除单个
function remove(button, row) {
  ElMessageBox.confirm('确认删除?', '提示', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      let ids = [row.id]
      await deleteAPI(tableName, ids)
      ElMessage.success('删除成功')
      fetchData()
    })
    .catch(() => {})
}
// 删除多个
function removes() {
  if (!selectedDatas.value.length) {
    ElMessage.error('请先框选要删除的数据')
    return
  }
  ElMessageBox.confirm('确认批量删除?', '提示', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      let ids = selectedDatas.value.map(item => item.id)
      await deleteAPI(tableName, ids)
      ElMessage.success('删除成功')
      selectedDatas.value = []
      fetchData()
    })
    .catch(() => {})
}

// ----------------------------------
// ---------- 查看组件 ---------------
// ----------------------------------
function view(button, row) {
  dialogVisible.value = true
  dialogTitle.value = button.title
  dialogComponent.value = ListView
  dialogClass.value = ''
  dialogData = {
    row,
  }
}

// ----------------------------------
// ---------- 编辑组件 ---------------
// ----------------------------------
// 新增
function add(button) {
  dialogTitle.value = button.title
  dialogComponent.value = ListEdit
  dialogClass.value = ''
  dialogData = {
    type: 'add', // add: 新增 update: 编辑 cross: 跨表
    id: '',
    tableName,
    defaultData: {
      ...route.params,
      ...route.query,
    },
    okText: '提交',
    cancleText: '取消',
  }
  dialogVisible.value = true
}
// 修改
function edit(button, row) {
  dialogTitle.value = button.title
  dialogClass.value = ''
  dialogComponent.value = ListEdit
  dialogData = {
    type: 'update',
    id: row.id,
    tableName,
    row,
    okText: '提交',
    cancleText: '取消',
  }
  dialogVisible.value = true
}
// ----------------------------------
// ---------- 跨表功能 ---------------
// ----------------------------------
async function crossTableHander(button, row) {
  let { name, crossType } = button
  let tableConfig = tableConfigs[tableName]
  let { table, columns } = tableConfig
  let { sfsh, isReverse, virtualPay } = table
  let index = table.crossOptButton.findIndex(buttonName => buttonName === name)
  // 跨表的关联数据
  // 审核权限
  let crossOptAudit = table.crossOptAudit[index]
  let crossOptPay = table.crossOptPay[index]
  // 提示
  let tips = table.crossOptButtonTips[index]
  // 状态字段
  let statusColumnName = table.crossOptButtonStatusColumns[index]
  // 新表
  let newTableName = table.crossOptTableName[index]

  // [1] 退出条件判断
  // 已开启审核功能，且未审核状态
  if (sfsh == '是' && crossOptAudit === '是' && row.sfsh != '是') {
    ElMessage.info('请审核通过后再操作')
    return
  }


  // 倒计时
  if (isReverse == '是' && virtualPay != '是') {
    if (dayjs().isAfter(dayjs(row.reversetime))) {
      ElMessage.info('倒计时已结束')
      return
    }
  }


  // 次数/状态限制
  let statusColumnValue
  let isLimit = false
  if (statusColumnName) {
    if (statusColumnName.startsWith('[')) {
      isLimit = true
      // 限制次数   从 [1] 提取 次数 1
      let limitNum = statusColumnName.replace(/\[|\]/g, '')
      limitNum = Number(limitNum)

      // 查询当前次数
      let params = {
        crossrefid: row.id,
        crossuserid: Number(localStorage.getItem('userid')),
      }
      // inspectiontime 日期条件
      let hasInspectiontime = tableConfigs[newTableName].columns.some(column => column.columnName == 'inspectiontime')
      if (hasInspectiontime) {
        let inspectiontime = dayjs().format('YYYY-MM-DD')
        params.inspectiontimestart = inspectiontime
        params.inspectiontimeend = inspectiontime
      }
      
      let res = await getPageAPI(newTableName, params)

      if (res.data.total >= limitNum) {
        ElMessage.error(tips)
        return
      }
    } else {
      // 状态限制
      let { customize } = columns.find(column => column.columnName === statusColumnName)
      // 关联的字段，约定是单选类型、且取的是选项一的值 customize: '已取消,已预约'-> statusColumnValue: '已取消'
      statusColumnValue = customize.split(',')[0]
      if (row[statusColumnName] === statusColumnValue) {
        ElMessage.success(tips)
        return
      }
    }
  }

  switch (crossType) {
    case 1:
      // 弹出编辑框
      dialogTitle.value = button.title
      dialogClass.value = ''
      dialogComponent.value = ListEdit
      dialogData = {
        type: 'cross',
        id: row.id,
        tableName: newTableName,
        crossData: {
          crossType,
          isLimit,
          statusColumnName,
          statusColumnValue,
          oldRow: row,
          oldTableName: tableName,
          newTableName,
        },
        okText: '提交',
        cancleText: '取消',
      }

      dialogVisible.value = true
      break
      

   }
}

// ----------------------------------
// ---------- 导出功能 ---------------
// ----------------------------------
function exportExcel() {
  // 获取当前表的columns配置
  let columns = getColums(tableName, 'view')

  // 一个sheet表数据
  let wsData = []

  // 第一行表头
  let headerRow = columns.map(column => column.comments)
  wsData.push(headerRow)

  // 其余行数据
  datas.value.forEach(item => {
    let row = columns.map(column => item[column.columnName])

    wsData.push(row)
  })

  const wb = utils.book_new()
  const ws = utils.aoa_to_sheet(wsData)
  utils.book_append_sheet(wb, ws, 'Sheet1')
  writeFileXLSX(wb, `${tableName}.xlsx`)

  ElMessage.success('导出成功')
}

// ----------------------------------
// ---------- 导入功能 ---------------
// ----------------------------------
// 导入
function importExcel(button) {
  dialogTitle.value = button.title
  dialogClass.value = ''
  dialogComponent.value = UploadXlsx
  dialogData = {
    type: 'import', // import: 导入 template: 上传模板
    title: button.title,
  }
  dialogVisible.value = true
}
// 上传模板
function uploadTemplate(button) {
  dialogTitle.value = button.title
  dialogClass.value = ''
  dialogComponent.value = UploadXlsx
  dialogData = {
    type: 'template',
    title: button.title,
  }

  dialogVisible.value = true
}
// 下载模板
async function downloadTemplate() {
  try {
    let fileName = `${tableName}_template.xlsx`
    await downloadFile(fileName)

    ElMessage.success('下载模板成功')
  } catch (error) {
    ElMessage.error('下载模板失败')
  }
}


// ----------------------------------
// ---------- 图表功能 ---------------
// ----------------------------------
function showChart(button) {
  let { title } = button
  dialogData = chartData.find(item => item.tableName === tableName && item.title == title)
  dialogData = {
    ...dialogData,
    title: ''
  }

  dialogClass.value = 'list-chart-wrapper'
  dialogComponent.value = ChartEntry
  dialogTitle.value = title
  dialogVisible.value = true
}










// ----------------------------------
// ------------ 预测 ----------------
// ----------------------------------
let isForecastLoading = false
// 预测: 带参数
async function forecast(button, row) {
  if (isForecastLoading) {
    ElMessage.warning('预测中，请耐心等待下。')
    return
  }
  ElMessage.info({
    message: '预测中... ...',
    duration: 0,
  })
  isForecastLoading = true

  try {
    // predictionChValueColumns 预测字段的字符串: 'address,totalprice,area,type'
    let { predictionChValueColumns = '' } = button
    let predictNames = predictionChValueColumns.split(',')
    let apiData = {
      id: row.id,
    }
    predictNames.forEach(name => {
      apiData[name] = row[name]
    })

    await predictAPI(tableName, apiData)
    await fetchData()
    ElMessage.closeAll()
    ElMessage.success('数据预测完成')
  } catch (error) {
    ElMessage.closeAll()
    ElMessage.error(error.message || error.msg || '预测失败！')
  }

  isForecastLoading = false
}
// 不带参数
async function forecast2() {
  if (isForecastLoading) {
    ElMessage.warning('预测中，请耐心等待下。')
    return
  }
  ElMessage.info({
    message: '预测中... ...',
    duration: 0,
  })
  isForecastLoading = true

  try {
    await predictAPI(tableName)
    await fetchData()
    ElMessage.closeAll()
    ElMessage.success('数据预测完成')
  } catch (error) {
    ElMessage.closeAll()
    ElMessage.error(error.message || error.msg || '预测失败！')
  }

  isForecastLoading = false
}
// 预测图表
async function forecastChart(button) {
  try {
    let res = await predictImgAPI(tableName)
    let imgList = res.data.map(item => {
      return {
        img: getFilePath(item),
        title: ''
      }
    })

    // 打开弹窗
    dialogTitle.value = button.title
    dialogClass.value = ''
    dialogComponent.value = CommonInfo
    dialogData = {
      mode: 'pictures',
      imgList,
    }
    dialogVisible.value = true
  } catch (error) {
    ElMessage.error(`查看预测图表失败！请尝试先点击【预测】按钮，再查看图表。`)
    ElMessage.error(error.message || error.msg)
  }
}
// ----------------------------------
// ------------ 预测 ----------------
// ----------------------------------
async function dataClean(){
  ElMessageBox.confirm('是否进行数据清洗?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      await cleanseAPI(tableName)
      ElMessage.success('数据清洗完成')
      fetchData()
    })
    .catch(() => {})  
}








// 拉取数据
async function fetchData(fetchParams) {
  isLoading.value = true
  try {
    let apiFn = listMode.value === 'recommend' ? getAutoSort2API : getPageAPI
    let apiTableName = tableName
    let _params = {}

    // 特殊表，微调一些参数
    switch (tableName) {



    }

    let params = {
      limit: pageSize.value,
      page: currentPage.value,

      ..._params,

      // 排序
      ...sortData.value,

      // 订单的status参数
      ...route.params,

      // query参数
      ...route.query,

      // 搜索参数
      ...searchData.value,

      ...fetchParams,
    }


    let res = await apiFn(apiTableName, params)

    datas.value = res.data.list
    total.value = res.data.total
    selectedDatas.value.length && (selectedDatas.value = [])
  } catch (error) {
    ElMessage.error(error.msg || error.message || '未知原因')
  }
  isLoading.value = false
}

watchEffect(() => {
  fetchData()
})
</script>

<template>
  <div class="list-wrapper">
    <!-- 搜索 -->
    <ListSearch :tableName="tableName" buttonName="查询" @search="searchEvent" />

    <!-- 按钮 -->
    <div class="header-button-wrapper" v-if="headerButtons.length">
      <el-button
        v-for="item in headerButtons"
        :key="item.key"
        :class="item.className"
        :icon="item.iconName"
        @click="headerEvent(item)"
      >
        {{ item.title }}
      </el-button>
    </div>
    <!-- 表格 -->
    <el-table
      v-loading="isLoading"
      :data="datas"
      row-key="id"
      @selection-change="selectionChange"
      @sort-change="sortChangeEvent"
      :default-sort="defaultSort"
      :border="false"
      :show-overflow-tooltip="true"
    >
      <el-table-column type="selection" :width="100" />

      <!-- 首列配置了fixed -->
      <el-table-column
        v-for="(column, index) in columns"
        :fixed="index === 0"
        min-width="150"
        align="left"
        :resizable="false"
        :prop="column.columnName"
        :label="column.comments"
        :key="column.columnName"
        :sortable="table.sortName && table.sortName == column.columnName ? 'custom' : false"
      >
        <template #default="scope">
          <component
            :is="column.table_type"
            :tableName="tableName"
            :row="scope.row"
            :column="column"
            :value="scope.row[column.columnName]"
          />
        </template>
      </el-table-column>

      <!-- 操作 -->
      <el-table-column
        fixed="right" 
        label="操作" 
        min-width="300" 
        v-if="tableButtons.length"
      >
        <template #default="{ row }">
          <div class="table-button-wrapper">
            <el-button
              v-for="item in tableButtons"
              v-show="getShow_tableButtons(item, row)"                       
              :key="item.key"
              :class="item.className"
              :icon="item.iconName"
              @click="actionEvent(item, row)"
              size="small"
            >
              {{ item.title }}
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="pageSizes"
        :total="total"
        :background="true"
        :layout="layout"
        :hide-on-single-page="false"
      />
    </div>

    <!-- 弹框公用 -->
    <el-dialog
      class="yy-dialog"
      v-model="dialogVisible"
      :title="dialogTitle"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <component
        v-model="dialogVisible"
        :is="dialogComponent"
        :tableName="tableName"
        :data="dialogData"
        :class="dialogClass"
        @fetchData="fetchData"
        @openDialog="openDialog"
      />
    </el-dialog>

  </div>
</template>
