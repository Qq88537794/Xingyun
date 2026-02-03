<template>
  <div class="h-full flex flex-col bg-white">
    <!-- Header (Hidden in tab mode) -->
    <!--
    <div class="px-4 py-3 border-b border-gray-200 flex justify-between items-center bg-gray-50">
      <h3 class="font-medium text-gray-700">样式编辑</h3>
      <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
        <X :size="16" />
      </button>
    </div>
    -->

    <!-- Content -->
    <div v-if="styleData" class="flex-1 overflow-y-auto p-4 space-y-6">
      <div class="space-y-2">
        <label class="block text-xs font-medium text-gray-500 uppercase">名称</label>
        <div class="text-sm font-bold text-gray-800">{{ styleData.label }}</div>
      </div>

      <!-- 字体设置 -->
      <div class="space-y-3">
        <label class="block text-xs font-medium text-gray-500 uppercase">排版</label>
        
        <div>
            <label class="text-xs text-gray-400 mb-1 block">字体</label>
            <select 
                v-model="localStyle.fontFamily" 
                class="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:border-blue-500 focus:outline-none"
            >
                <option value="">默认</option>
                <option 
                    v-for="font in displayFonts" 
                    :key="font.value" 
                    :value="font.value"
                >
                    {{ font.label }}
                </option>
            </select>
        </div>

        <div class="grid grid-cols-2 gap-3">
            <div>
                 <label class="text-xs text-gray-400 mb-1 block">字号</label>
                 <!-- 字号选择组件 (仿 Word) -->
                 <div class="relative w-full">
                    <div class="flex items-center w-full border border-gray-300 rounded px-2 py-1 bg-white hover:border-blue-400 transition-colors h-[30px]">
                        <input 
                            v-model="currentSizeInput"
                            @keydown.enter="handleSizeInputConfirm"
                            @blur="handleSizeInputConfirm"
                            class="w-full text-sm border-none focus:outline-none text-gray-700 bg-transparent p-0"
                            placeholder="字号"
                        />
                        <button 
                            @click="showSizeMenu = !showSizeMenu"
                            class="ml-1 flex-shrink-0 text-gray-500 hover:text-gray-700 focus:outline-none"
                        >
                            <ChevronDown :size="14" />
                        </button>
                    </div>
                    
                    <!-- 下拉菜单 -->
                    <div 
                      v-if="showSizeMenu"
                      class="absolute top-full left-0 mt-1 w-full bg-white rounded shadow-xl border border-gray-200 py-1 z-50 max-h-60 overflow-y-auto"
                    >
                       <button
                         v-for="size in displayFontSizes"
                         :key="size.pt"
                         @click="setSize(size.pt)"
                         class="w-full text-left px-3 py-1.5 text-sm hover:bg-gray-100 flex justify-between items-center group"
                       >
                         <span>{{ size.pt }}</span>
                         <span v-if="size.label" class="text-gray-400 text-xs">{{ size.label }}</span>
                       </button>
                    </div>
                    
                    <div v-if="showSizeMenu" @click="showSizeMenu = false" class="fixed inset-0 z-40" style="cursor: default;"></div>
                 </div>
            </div>
            <div>
                 <label class="text-xs text-gray-400 mb-1 block">行高</label>
                 <input 
                    type="number" 
                    step="0.1"
                    v-model="localStyle.lineHeight"
                    class="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:border-blue-500 focus:outline-none h-[30px]"
                 />
            </div>
        </div>

        <div class="flex items-center space-x-2 pt-2">
            <label class="flex items-center space-x-2 cursor-pointer select-none">
                <input type="checkbox" v-model="localStyle.bold" class="rounded text-blue-600 focus:ring-blue-500" />
                <span class="text-sm text-gray-700">加粗</span>
            </label>
             <label class="flex items-center space-x-2 cursor-pointer select-none">
                <input type="checkbox" v-model="localStyle.italic" class="rounded text-blue-600 focus:ring-blue-500" />
                <span class="text-sm text-gray-700">斜体</span>
            </label>
        </div>
      </div>

       <!-- 颜色设置 -->
       <div class="space-y-3">
        <label class="block text-xs font-medium text-gray-500 uppercase">颜色</label>
        <div class="flex items-center space-x-3">
          <input 
            type="color" 
            v-model="localStyle.color"
            class="h-8 w-8 p-0 border-0 rounded overflow-hidden cursor-pointer"
          />
          <span class="text-sm text-gray-600">{{ localStyle.color }}</span>
        </div>
      </div>

      <!-- 间距设置 -->
       <div class="space-y-3">
        <label class="block text-xs font-medium text-gray-500 uppercase">间距</label>
        
        <div class="grid grid-cols-2 gap-3">
            <div>
                 <label class="text-xs text-gray-400 mb-1 block">段前 (em)</label>
                 <input 
                    type="number" 
                    step="0.1"
                    v-model="localStyle.marginTop"
                    class="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:border-blue-500 focus:outline-none"
                 />
            </div>
            <div>
                 <label class="text-xs text-gray-400 mb-1 block">段后 (em)</label>
                 <input 
                    type="number" 
                    step="0.1"
                    v-model="localStyle.marginBottom"
                    class="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:border-blue-500 focus:outline-none"
                 />
            </div>
        </div>
       </div>

    </div>

    <!-- Placeholder when no style selected -->
    <div v-else class="flex-1 flex flex-col items-center justify-center text-gray-400 p-8 text-center bg-gray-50">
       <div class="mb-4 text-gray-300">
           <!-- Icon placeholder -->
           <svg class="w-12 h-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
           </svg>
       </div>
       <p class="text-sm">请在工具栏选择一个样式进行编辑</p>
    </div>

    <!-- Footer -->
    <div v-if="styleData" class="p-4 border-t border-gray-200 bg-gray-50 flex justify-end space-x-2">
      <button 
        @click="$emit('close')"
        class="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-200 rounded"
      >
        取消
      </button>
      <button 
        @click="save"
        class="px-3 py-1.5 text-sm bg-blue-600 text-white hover:bg-blue-700 rounded shadow-sm"
      >
        保存应用
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { X, ChevronDown } from 'lucide-vue-next'

const props = defineProps({
  styleData: {
    type: Object,
    default: null // Allow null
  },
  systemFonts: {
      type: Array,
      default: () => []
  }
})

const displayFonts = computed(() => {
    if (props.systemFonts && props.systemFonts.length > 0) {
        return props.systemFonts
    }
    return [
       { label: '微软雅黑', value: '"Microsoft YaHei"' },
       { label: '宋体', value: 'SimSun' },
       { label: '黑体', value: 'SimHei' },
       { label: '楷体', value: 'KaiTi' },
       { label: 'FangSong', value: 'FangSong' },
       { label: 'Arial', value: 'Arial' },
       { label: 'Times New Roman', value: '"Times New Roman"' }
    ]
})

const emit = defineEmits(['close', 'save'])

const localStyle = ref({
    fontSize: 16,
    lineHeight: 1.5,
    bold: false,
    italic: false,
    color: '#000000',
    marginTop: 1,
    marginBottom: 1,
    fontFamily: ''
})

/* 字号相关逻辑 */
const showSizeMenu = ref(false)
const currentSizeInput = ref('')

const fontSizes = [
  { pt: 42, label: '初号' },
  { pt: 36, label: '小初' },
  { pt: 26, label: '一号' },
  { pt: 24, label: '小一' },
  { pt: 22, label: '二号' },
  { pt: 18, label: '小二' },
  { pt: 16, label: '三号' },
  { pt: 15, label: '小三' },
  { pt: 14, label: '四号' },
  { pt: 12, label: '小四' },
  { pt: 10.5, label: '五号' },
  { pt: 9, label: '小五' },
  { pt: 7.5, label: '六号' },
  { pt: 6.5, label: '小六' },
  { pt: 5.5, label: '七号' },
  { pt: 5, label: '八号' },
]

const otherSizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 72]

const displayFontSizes = computed(() => {
    const list = [...fontSizes]
    otherSizes.forEach(pt => {
        if (!list.find(item => item.pt === pt)) {
             list.push({ pt, label: '' })
        }
    })
    return list.sort((a, b) => a.pt - b.pt)
})

// 将 px 转为 pt 的显示值
const updateSizeInputFromPx = (px) => {
    if (!px) {
        currentSizeInput.value = ''
        return
    }
    // px -> pt: pt = px * 0.75
    // round to nearest 0.5
    const pt = Math.round((px * 0.75) * 2) / 2
    
    // Check if matches a Chinese label
    const exactMatch = fontSizes.find(f => f.pt === pt)
    
    // 如果是预设的字号，还是优先显示字号数值，但在 dropdown 里会高亮
    // 但用户要求 "支持中文字体格式（如小初）"，意味着如果匹配，输入框里也许可以显示名字？
    // EditorToolbar里是怎么做的？currentSizeInput.value = pt.toString()。它只显示数字。
    // 但用户说 "输入框...支持中文字体格式"。 Toolbar支持输入 "五号" 然后回车应用。
    // 我们这里保持 input 是 pt 数值简单点，或者也支持输入中文。
    // 但是这里是 update FROM model。Model is px.
    // Let's just show the pt number.
    currentSizeInput.value = pt.toString()
}

watch(() => localStyle.value.fontSize, (newPx) => {
    updateSizeInputFromPx(newPx)
})

const setSize = (pt) => {
    // pt -> px: px = pt / 0.75
    const px = pt / 0.75
    // Keep 2 decimals to be safe
    localStyle.value.fontSize = Math.round(px * 100) / 100
    showSizeMenu.value = false
    currentSizeInput.value = pt.toString()
}

const handleSizeInputConfirm = () => {
   let val = currentSizeInput.value.trim()
   // 检查是否是中文名
   const chineseSize = fontSizes.find(f => f.label === val)
   if (chineseSize) {
       setSize(chineseSize.pt)
       return
   }
   
   // 检查是否是数字
   const num = parseFloat(val)
   if (!isNaN(num) && num > 0) {
       setSize(num)
   } else {
       // 无效输入，重置回当前值
       updateSizeInputFromPx(localStyle.value.fontSize)
   }
   // 使输入框失去焦点
   if (document.activeElement && document.activeElement.tagName === 'INPUT') {
       document.activeElement.blur()
   }
}

// Initialize local state from props
const init = () => {
    if (props.styleData && props.styleData.style) {
        localStyle.value = { ...localStyle.value, ...props.styleData.style }
        updateSizeInputFromPx(localStyle.value.fontSize)
    }
}

watch(() => props.styleData, init, { immediate: true })

const save = () => {
    emit('save', {
        id: props.styleData.id,
        style: { ...localStyle.value }
    })
}
</script>