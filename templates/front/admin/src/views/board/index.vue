<script setup>
/**
 * @description 看板
 * 由 表格、图文、地图、总数统计、图表 组成
 */

import "@/style/board.scss";
import { onMounted } from 'vue'
import { useRouter } from "vue-router";
// 图表
import chartData from "@/components/Echart/chartData";

import Chart from "./Chart.vue";
import Image from "./Image.vue";
import Map from "./Map.vue";
import Statics from "./Statics.vue";
import Table from "./Table.vue";
import Forecast from "./Forecast.vue";
const runIdle =
  globalThis.requestIdleCallback || ((callback) => setTimeout(callback, 1))
const typeMap = {
  multiStatic: Chart,
  image: Image,
  table: Table,
  map: Map,
  statics: Statics,
  forecast: Forecast,
};

const router = useRouter();

// ----------------------------------
// ---------- 表格或图文 -------------
// ----------------------------------
let tableOrImageData = [
  {
    type: 'table',
    tableName: 'drivinglog',
    title: '行车日志',
    textNames: [
      {
        key: 'vehiclenumber',
        title: '车辆编号'
      },
      {
        key: 'vehiclemodel',
        title: '车辆型号'
      },
      {
        key: 'batterycapacity',
        title: '电池容量'
      },
      {
        key: 'batterylife',
        title: '电池寿命/月'
      },
      {
        key: 'accumulatedmileage',
        title: '行驶里程'
      },
      {
        key: 'rapidaccelerationtimes',
        title: '急加速次数'
      },
      {
        key: 'numberofrapiddecelerations',
        title: '急减速次数'
      },
      {
        key: 'numberofspeedingincidents',
        title: '超速次数'
      },
      {
        key: 'energysavingsuggestions',
        title: '节能建议'
      },
      {
        key: 'drivingbehaviorrating',
        title: '驾驶行为评分'
      },
    ],
    imgKey: '',
    imgTitle: ''
  },
]

// ----------------------------------
// ---------- 地图 ------------------
// ----------------------------------
let mapData = chartData.find(item => item.graphType.startsWith('地') && item.chartSort == '0')
if (mapData) {
  mapData.type = 'map'
}

// ----------------------------------
// ---------- 总数统计 ---------------
// ----------------------------------
let staticsData = {
  type: 'statics',
  list: [
    {
      tableName: 'drivinglog',
      comments: '行车日志',
    },
  ]
}

// ----------------------------------
// ---------- 分配 ------------------
// ----------------------------------
// 1-10的位置
const seatList = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"];
// 位置的前缀,与seatList的item组成key hasEchart1 hasEchart2...
const seatPre = "hasEchart";
// 图表 + 表格 + 图文 数据,1-10,最多10个
let seatDatas = {};

// 1.1 添加 图表
chartData.forEach((item) => {
  let { chartSort } = item;
  if (chartSort && chartSort != "0") {
    let key = seatPre + chartSort;
    seatDatas[key] = item;
  }
});

// 1.2 添加 表格、图文
let tableOrImageData_copy = tableOrImageData.slice(0);
for (let index = 0; index < seatList.length; index++) {
  let key = "hasEchart" + seatList[index];

  // 没有tableOrImageData数据,终止
  if (!tableOrImageData_copy.length) {
    break;
  }

  // configData已经有数据,往下走
  if (seatDatas[key]) {
    continue;
  }

  // 添加数据
  let item = tableOrImageData_copy.splice(0, 1)[0];
  // 新增chartSort 属性
  item.chartSort = seatList[index];
  seatDatas[key] = item;
}

// 2. 形成新的列表数据

let leftBase = {"hasEchart3":true,"hasEchart4":false,"hasForecast":false,"hasStatics":false,"hasTable":false,"hasMap":false,"hasSys":false,"hasIdea1":false,"hasEchart1":true,"hasEchart2":true}
let centerBase = {"hasEchart3":false,"hasEchart4":false,"hasEchart5":false,"hasForecast":false,"hasEchart6":true,"hasStatics":true,"hasTable":true,"hasMap":true,"hasSys":false,"hasEchart1":false,"hasEchart2":false}
let rightBase = {"hasEchart3":false,"hasEchart4":true,"hasEchart5":true,"hasForecast":true,"hasStatics":false,"hasTable":false,"hasMap":false,"hasSys":false,"hasEchart1":false,"hasEchart2":false}

let leftList = getShowItems(leftBase, seatDatas);
let centerList = getShowItems(centerBase, seatDatas);
let rightList = getShowItems(rightBase, seatDatas);

// 图文、表格的动画配置
let animation = {
  time: parseInt(2000),
  flag: true,
}

/**
 * @description 把是否显示的配置项 + 图表数据,重新生成一个要显示的列表
 * @returns
 */
function getShowItems(inputBase) {
  let list = [];

  // 地图
  if (inputBase.hasMap && mapData) {
    list.push(mapData);
  }

  // 总数统计
  if (inputBase.hasStatics) {
    list.push(staticsData);
  }

  // 图表、图文、表格,1-10位置
  seatList.forEach((item) => {
    let key = "hasEchart" + item;
    if (inputBase[key] && seatDatas[key]) {
      list.push(seatDatas[key]);
    }
  });

  // 预测
  if (inputBase.hasForecast) {
    list.push({
      type: 'forecast'
    }) 
  }

  return list;
}

onMounted(() => {
  setTimeout(() => {
    runIdle(() => {
      // 提前加载 首页
      import ('@/views/home/home.vue')
    });
  }, 1000);
});
</script>

<template>
  <div class="board">
    <!-- 粒子效果 -->

    <!-- 头部 -->
    <div class="header">
      <!-- 标题 -->
      <div class="title">{{ projectName }}</div>

      <!-- 回首页 -->
      <div class="time">
        <el-button
          type="primary"
          icon="HomeFilled"
          text
          @click="router.push('/home')"
        >
          回首页
        </el-button>
      </div>
    </div>

    <!-- 内容: 左、中、右布局 -->
    <div class="wrapper">
      <div class="left">
        <component
          v-for="(item, index) in leftList"
          :is="typeMap[item.type]"
          :key="index"
          :configData="item"
          :animation="animation"
        />
      </div>

      <div class="center">
        <component
          v-for="(item, index) in centerList"
          :is="typeMap[item.type]"
          :key="index"
          :configData="item"
          :animation="animation"
        />
      </div>

      <div class="right">
        <component
          v-for="(item, index) in rightList"
          :is="typeMap[item.type]"
          :key="index"
          :configData="item"
          :animation="animation"
        />
      </div>
    </div>
  </div>
</template>
