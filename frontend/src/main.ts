import { createApp } from 'vue'
import { createPinia } from 'pinia'
import {
  ElButton,
  ElCheckbox,
  ElCheckboxGroup,
  ElDescriptions,
  ElDescriptionsItem,
  ElDialog,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElLoading,
  ElOption,
  ElOptionGroup,
  ElPagination,
  ElProgress,
  ElSelect,
  ElSwitch,
  ElTabPane,
  ElTable,
  ElTableColumn,
  ElTabs,
  ElTag,
  ElUpload,
} from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import {
  Aim,
  CircleCloseFilled,
  Connection,
  DataAnalysis,
  Document,
  Expand,
  Files,
  Fold,
  Loading,
  Monitor,
  Search,
  Setting,
  SuccessFilled,
  Switch,
  Upload,
} from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, DataZoomComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import router from './router'
import App from './App.vue'
import './style.css'

use([CanvasRenderer, LineChart, PieChart, BarChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent])

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElLoading)

const elementComponents = [
  ElButton,
  ElCheckbox,
  ElCheckboxGroup,
  ElDescriptions,
  ElDescriptionsItem,
  ElDialog,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElOption,
  ElOptionGroup,
  ElPagination,
  ElProgress,
  ElSelect,
  ElSwitch,
  ElTabPane,
  ElTable,
  ElTableColumn,
  ElTabs,
  ElTag,
  ElUpload,
]

for (const component of elementComponents) {
  app.component(component.name!, component)
}

const elementIcons = {
  Aim,
  CircleCloseFilled,
  Connection,
  DataAnalysis,
  Document,
  Expand,
  Files,
  Fold,
  Loading,
  Monitor,
  Search,
  Setting,
  SuccessFilled,
  Switch,
  Upload,
}

for (const [key, component] of Object.entries(elementIcons)) {
  app.component(key, component)
}
app.component('v-chart', VChart)

app.mount('#app')
