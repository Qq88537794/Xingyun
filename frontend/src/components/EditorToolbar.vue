<template>
  <div class="editor-toolbar bg-gray-50 border-b border-gray-200 px-4 py-2 flex items-center flex-wrap gap-1">
    <!-- 撤销/重做 -->
    <div class="flex items-center space-x-1 border-r border-gray-300 pr-2 mr-1">
      <button 
        @click="editor.chain().focus().undo().run()"
        :disabled="!editor.can().undo()"
        class="toolbar-btn"
        title="撤销 (Ctrl+Z)"
      >
        <Undo :size="16" />
      </button>
      <button 
        @click="editor.chain().focus().redo().run()"
        :disabled="!editor.can().redo()"
        class="toolbar-btn"
        title="重做 (Ctrl+Y)"
      >
        <Redo :size="16" />
      </button>
    </div>
    
    <!-- 文本格式 -->
    <div class="flex items-center space-x-1 border-r border-gray-300 pr-2 mr-1">
      <!-- 字体选择框 (仿 Word) -->
      <div class="relative w-32 mr-1">
        <button 
          @click="showFontMenu = !showFontMenu"
          class="flex items-center justify-between w-full px-2 py-1 bg-white border border-gray-200 hover:border-blue-400 rounded text-xs transition-colors h-8"
          title="字体"
        >
          <span class="truncate text-gray-700 font-medium">{{ currentFontLabel }}</span>
          <ChevronDown :size="12" class="text-gray-500 ml-1 flex-shrink-0" />
        </button>
        
        <!-- 下拉菜单 -->
        <div 
          v-if="showFontMenu"
          class="absolute top-full left-0 mt-1 w-48 bg-white rounded shadow-xl border border-gray-200 py-1 z-50 max-h-80 overflow-y-auto font-menu-scroll"
        >
          <!-- 最近使用 -->
          <template v-if="recentFonts.length > 0">
            <button
              v-for="font in recentFonts"
              :key="'recent-' + font.label"
              @click="setFont(font)"
              class="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 flex justify-between items-center group"
              :class="{ 'bg-blue-50 text-blue-700': currentFontLabel === font.label }"
            >
              <span :style="{ fontFamily: font.value || 'inherit' }" class="truncate">
                {{ font.label }}
              </span>
            </button>
            <!-- 分割线: 加粗并调整边距 -->
            <div class="border-b-2 border-gray-200 my-2 mx-2"></div>
          </template>

          <!-- 系统字体 (已排序) -->
          <button
            v-for="font in sortedSystemFonts"
            :key="font.label"
            @click="setFont(font)"
            class="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 flex justify-between items-center group"
            :class="{ 'bg-blue-50 text-blue-700': currentFontLabel === font.label }"
          >
            <span :style="{ fontFamily: font.value || 'inherit' }" class="truncate">
              {{ font.label }}
            </span>
          </button>
        </div>
        
        <!-- 点击外部关闭遮罩 -->
        <div v-if="showFontMenu" @click="showFontMenu = false" class="fixed inset-0 z-40" style="cursor: default;"></div>
      </div>

      <!-- 字号选择框 -->
      <div class="relative w-20 mr-1">
        <div class="flex items-center w-full bg-white border border-gray-200 hover:border-blue-400 rounded transition-colors h-8">
            <input 
                v-model="currentSizeInput"
                @keydown.enter="handleSizeInputConfirm"
                @blur="handleSizeInputConfirm"
                class="font-size-input w-full px-1 py-1 text-xs border-none focus:outline-none text-gray-700 font-medium bg-transparent text-center"
                title="字号"
            />
            <button 
                @click="showSizeMenu = !showSizeMenu"
                class="px-0.5 h-full flex items-center justify-center border-l border-gray-100 hover:bg-gray-50 flex-shrink-0 w-5"
            >
                <ChevronDown :size="12" class="text-gray-500" />
            </button>
        </div>
        
        <!-- 下拉菜单 -->
        <div 
          v-if="showSizeMenu"
          class="absolute top-full left-0 mt-1 w-32 bg-white rounded shadow-xl border border-gray-200 py-1 z-50 max-h-80 overflow-y-auto font-menu-scroll"
        >
           <button
             v-for="size in displayFontSizes"
             :key="size.pt"
             @click="setSize(size.pt)"
             class="w-full text-left px-3 py-1 text-sm hover:bg-gray-100 flex justify-between items-center group leading-relaxed"
             :class="{ 'bg-blue-50 text-blue-700': currentFontSizePt === size.pt }"
           >
             <span>{{ size.pt }}</span>
             <span v-if="size.label" class="text-gray-400 text-xs transform scale-90 origin-right transition-colors group-hover:text-gray-500">{{ size.label }}</span>
           </button>
        </div>
        
         <div v-if="showSizeMenu" @click="showSizeMenu = false" class="fixed inset-0 z-40" style="cursor: default;"></div>
      </div>

       <!-- 字体颜色 -->
      <div class="relative flex items-center mr-1">
        <label 
          class="flex items-center justify-center w-8 h-8 rounded hover:bg-gray-100 cursor-pointer transition-colors relative"
          title="字体颜色"
        >
          <Baseline :size="16" :style="{ color: currentColor }" />
          <input 
            type="color" 
            ref="colorInput"
            @input="setColor"
            :value="currentColor"
            class="absolute opacity-0 w-full h-full cursor-pointer" 
          />
        </label>
      </div>

      <button 
        @click="editor.chain().focus().toggleBold().run()"
        :class="{ 'is-active': editor.isActive('bold') }"
        class="toolbar-btn"
        title="粗体 (Ctrl+B)"
      >
        <Bold :size="16" />
      </button>
      <button 
        @click="editor.chain().focus().toggleItalic().run()"
        :class="{ 'is-active': editor.isActive('italic') }"
        class="toolbar-btn"
        title="斜体 (Ctrl+I)"
      >
        <Italic :size="16" />
      </button>
      <button 
        @click="editor.chain().focus().toggleUnderline().run()"
        :class="{ 'is-active': editor.isActive('underline') }"
        class="toolbar-btn"
        title="下划线 (Ctrl+U)"
      >
        <UnderlineIcon :size="16" />
      </button>
      <button 
        @click="editor.chain().focus().toggleStrike().run()"
        :class="{ 'is-active': editor.isActive('strike') }"
        class="toolbar-btn"
        title="删除线"
      >
        <Strikethrough :size="16" />
      </button>
      <button 
        @click="editor.chain().focus().toggleCode().run()"
        :class="{ 'is-active': editor.isActive('code') }"
        class="toolbar-btn"
        title="行内代码"
      >
        <Code :size="16" />
      </button>
    </div>
    
    <!-- 样式 -->
    <div class="flex items-center space-x-1 border-r border-gray-300 pr-2 mr-1">
      <div class="relative w-24 mr-1">
        <button 
          @click="showStyleMenu = !showStyleMenu"
          class="flex items-center justify-between w-full px-2 py-1 bg-white border border-gray-200 hover:border-blue-400 rounded text-xs transition-colors h-8"
          title="样式"
        >
          <span class="truncate text-gray-700 font-medium">{{ currentStyleLabel }}</span>
          <ChevronDown :size="12" class="text-gray-500 ml-1 flex-shrink-0" />
        </button>
        
        <!-- 样式下拉菜单 -->
        <div 
          v-if="showStyleMenu"
          class="absolute top-full left-0 mt-1 w-64 bg-white rounded shadow-xl border border-gray-200 py-1 z-50 max-h-96 overflow-y-auto"
        >
          <div
            v-for="style in availableStyles"
            :key="style.id"
            class="group flex items-center justify-between px-3 py-2 hover:bg-gray-100 cursor-pointer"
            @click="applyStyle(style)"
          >
            <!-- 预览区域 -->
            <div class="flex-1 overflow-hidden mr-2">
                 <div :style="getPreviewStyle(style)" class="truncate">
                    {{ style.label }}
                 </div>
                 <div class="text-xs text-gray-400 mt-0.5 truncate">
                    {{ style.element }}
                 </div>
            </div>
            
            <!-- 编辑按钮 -->
            <button 
                @click="editStyle(style, $event)"
                class="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded opacity-0 group-hover:opacity-100 transition-all"
                title="修改样式"
            >
                <Settings :size="14" />
            </button>
          </div>
        </div>
        
        <div v-if="showStyleMenu" @click="showStyleMenu = false" class="fixed inset-0 z-40" style="cursor: default;"></div>
      </div>

    </div>
    
    <!-- 列表和引用 -->
    <div class="flex items-center space-x-1 border-r border-gray-300 pr-2 mr-1">
      <button 
        @click="editor.chain().focus().toggleBulletList().run()"
        :class="{ 'is-active': editor.isActive('bulletList') }"
        class="toolbar-btn"
        title="无序列表"
      >
        <List :size="16" />
      </button>
      <button 
        @click="editor.chain().focus().toggleOrderedList().run()"
        :class="{ 'is-active': editor.isActive('orderedList') }"
        class="toolbar-btn"
        title="有序列表"
      >
        <ListOrdered :size="16" />
      </button>
      <button 
        @click="editor.chain().focus().toggleBlockquote().run()"
        :class="{ 'is-active': editor.isActive('blockquote') }"
        class="toolbar-btn"
        title="引用"
      >
        <Quote :size="16" />
      </button>
      <button 
        @click="editor.chain().focus().toggleCodeBlock().run()"
        :class="{ 'is-active': editor.isActive('codeBlock') }"
        class="toolbar-btn"
        title="代码块"
      >
        <FileCode :size="16" />
      </button>
    </div>
    
    <!-- 插入 -->
    <div class="flex items-center space-x-1 border-r border-gray-300 pr-2 mr-1">
      <div class="relative">
        <button 
          @click="showImageMenu = !showImageMenu"
          class="toolbar-btn"
          title="插入图片"
        >
          <ImageIcon :size="16" />
        </button>
        <!-- 图片菜单 -->
        <div 
          v-if="showImageMenu" 
          class="absolute top-full left-0 mt-1 w-64 bg-white rounded shadow-xl border border-gray-200 py-1 z-50 flex flex-col"
        >
          <div v-if="imageMenuStep === 'list'" class="flex flex-col">
            <button 
              @click="triggerImageUpload" 
              class="text-left px-3 py-2 text-sm hover:bg-gray-100 flex items-center space-x-2"
            >
              <span>本地上传</span>
            </button>
            <button 
              @click="showUrlInput" 
              class="text-left px-3 py-2 text-sm hover:bg-gray-100 flex items-center space-x-2"
            >
              <span>网络图片</span>
            </button>
          </div>
          
          <div v-else-if="imageMenuStep === 'url'" class="p-2 flex flex-col space-y-2">
            <input 
              ref="urlInputRef"
              v-model="imageUrlInput"
              type="text" 
              placeholder="https://..." 
              class="text-sm border rounded px-2 py-1 w-full focus:outline-none focus:border-blue-400"
              @keydown.enter="confirmImageUrl"
              @keydown.esc="cancelUrlInput"
            />
            <div class="flex justify-end space-x-1">
              <button 
                @click="cancelUrlInput"
                class="px-2 py-1 text-xs text-gray-500 hover:bg-gray-100 rounded"
              >
                取消
              </button>
              <button 
                @click="confirmImageUrl"
                class="px-2 py-1 text-xs bg-blue-500 text-white hover:bg-blue-600 rounded"
              >
                插入
              </button>
            </div>
          </div>
        </div>
        <div v-if="showImageMenu" @click="showImageMenu = false" class="fixed inset-0 z-40" style="cursor: default;"></div>
        <input 
          type="file" 
          ref="imageInput" 
          class="hidden" 
          accept="image/*" 
          @change="handleImageFile" 
        />
      </div>

      <button 
        @click="insertTable"
        class="toolbar-btn"
        title="插入表格"
      >
        <TableIcon :size="16" />
      </button>
      <button 
        @click="editor.chain().focus().setHorizontalRule().run()"
        class="toolbar-btn"
        title="分割线"
      >
        <Minus :size="16" />
      </button>
    </div>
    
    <!-- AI 功能（需要后端） -->
    <div class="flex items-center space-x-1">
      <button 
        @click="handleAIGenerate"
        class="toolbar-btn-ai"
        title="AI 生成内容（需要后端）"
      >
        <Sparkles :size="16" />
      </button>
      <button 
        @click="handleAIOptimize"
        class="toolbar-btn-ai"
        title="AI 优化选中内容（需要后端）"
      >
        <Wand2 :size="16" />
      </button>
      <button 
        @click="handleInsertChart"
        class="toolbar-btn-ai"
        title="插入图表（需要后端）"
      >
        <BarChart3 :size="16" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { 
  Undo, Redo,
  Bold, Italic, Underline as UnderlineIcon, Strikethrough, Code,
  List, ListOrdered, Quote, FileCode,
  Image as ImageIcon, Table as TableIcon, Minus,
  Sparkles, Wand2, BarChart3,
  ChevronDown, Settings, Baseline
} from 'lucide-vue-next'
import { useToast } from '../composables/useToast'
import { uploadImage } from '../services/image'

const props = defineProps({
  editor: {
    type: Object,
    required: true
  },
  styles: {
      type: Array,
      default: () => []
  },
  systemFonts: {
      type: Array,
      default: () => []
  }
})

const emit = defineEmits(['edit-style'])

const toast = useToast()
const showFontMenu = ref(false)
const showImageMenu = ref(false)
const imageMenuStep = ref('list')
const imageUrlInput = ref('')
const urlInputRef = ref(null)
const imageInput = ref(null)
const recentFonts = ref([])

const sortedSystemFonts = computed(() => {
    // 优先使用传入的 systemFonts
    let fonts = []
    if (props.systemFonts && props.systemFonts.length > 0) {
        fonts = [...props.systemFonts]
    } else {
        fonts = [...rawSystemFonts]
    }

    // 这里可以添加额外排序逻辑如果需要，
    // 但 App.vue 传递进来的已经是排好序的了。
    // 如果是 rawSystemFonts，它本身是硬编码列表。
    return fonts
})

// 字体本地化映射表
const fontNameMap = {
  // Windows
  'Microsoft YaHei': '微软雅黑',
  'SimSun': '宋体',
  'NSimSun': '新宋体',
  'SimHei': '黑体',
  'KaiTi': '楷体',
  'FangSong': '仿宋',
  'DengXian': '等线',
  'YouYuan': '幼圆',
  'STXihei': '华文细黑',
  'STKaiti': '华文楷体',
  'STSong': '华文宋体',
  'STZhongsong': '华文中宋',
  'STFangsong': '华文仿宋',
  'STHupo': '华文琥珀',
  'STLiti': '华文隶书',
  'STXingkai': '华文行楷',
  'STXinwei': '华文新魏',
  
  // macOS
  'PingFang SC': '苹方',
  'Hiragino Sans GB': '冬青黑体',
  'Heiti SC': '黑体',
  'Songti SC': '宋体',
  'Kaiti SC': '楷体',
  'Lantinghei SC': '兰亭黑',
}

// 需要在顶部显示的优先字体
const priorityFonts = [
  'Microsoft YaHei', 'SimSun', 'SimHei', 'KaiTi', 'FangSong', 'PingFang SC'
]

onMounted(async () => {
  // 加载最近使用的字体
  const savedRecent = localStorage.getItem('recent_fonts')
  if (savedRecent) {
    try {
      recentFonts.value = JSON.parse(savedRecent)
    } catch (e) {
      console.warn('Failed to parse recent fonts')
    }
  }
})

// 默认基础回退字体库
const rawSystemFonts = [
  // --- 中文字体 (包含常见的英文名映射) ---
  { label: '微软雅黑', value: '"Microsoft YaHei", "Heiti SC", sans-serif', isChinese: true },
  { label: '宋体', value: 'SimSun, "Songti SC", serif', isChinese: true },
  { label: '黑体', value: 'SimHei, "Heiti SC", sans-serif', isChinese: true },
  { label: '楷体', value: 'KaiTi, "Kaiti SC", serif', isChinese: true },
  { label: '仿宋', value: 'FangSong, "FangSong SC", serif', isChinese: true },
  { label: '苹方', value: '"PingFang SC", sans-serif', isChinese: true },
  { label: '华文黑体', value: 'STHeiti, sans-serif', isChinese: true },
  { label: '华文楷体', value: 'STKaiti, serif', isChinese: true },
  { label: '华文宋体', value: 'STSong, serif', isChinese: true },
  { label: '幼圆', value: 'YouYuan, sans-serif', isChinese: true },
  
  // --- 英文字体 ---
  { label: 'Arial', value: 'Arial, sans-serif', isChinese: false },
  { label: 'Arial Black', value: '"Arial Black", sans-serif', isChinese: false },
  { label: 'Calibri', value: 'Calibri, sans-serif', isChinese: false },
  { label: 'Cambria', value: 'Cambria, serif', isChinese: false },
  { label: 'Comic Sans MS', value: '"Comic Sans MS", cursive', isChinese: false },
  { label: 'Courier New', value: '"Courier New", monospace', isChinese: false },
  { label: 'Georgia', value: 'Georgia, serif', isChinese: false },
  { label: 'Helvetica', value: 'Helvetica, sans-serif', isChinese: false },
  { label: 'Impact', value: 'Impact, sans-serif', isChinese: false },
  { label: 'Tahoma', value: 'Tahoma, sans-serif', isChinese: false },
  { label: 'Times New Roman', value: '"Times New Roman", serif', isChinese: false },
  { label: 'Trebuchet MS', value: '"Trebuchet MS", sans-serif', isChinese: false },
  { label: 'Verdana', value: 'Verdana, sans-serif', isChinese: false },
]

const currentFontLabel = computed(() => {
  if (!props.editor) return '微软雅黑'
  
  // 获取当前光标或选区的字体属性
  let activeFont = props.editor.getAttributes('textStyle').fontFamily

  // 如果没有直接的字体属性，尝试获取编辑器计算样式
  // 这确保了在未设置字体（如粘贴纯文本）时显示真实渲染的字体，而不是错误的默认值
  if (!activeFont && props.editor.view) {
    try {
      const { from } = props.editor.state.selection
      const dom = props.editor.view.domAtPos(from).node
      const element = dom.nodeType === 3 ? dom.parentElement : dom
      
      if (element) {
        const computed = window.getComputedStyle(element).fontFamily
        if (computed) {
          activeFont = computed
        }
      }
    } catch (e) {
      // Ignore errors
    }
  }
  
  if (!activeFont) return '微软雅黑' // 默认显示微软雅黑
  
  // 清理引号并只取第一个字体
  activeFont = activeFont.split(',')[0].trim().replace(/^['"]|['"]$/g, '')
  
  // 在已加载的系统字体中查找
  const knownFont = sortedSystemFonts.value.find(f => {
      const cleanName = f.value.split(',')[0].trim().replace(/^['"]|['"]$/g, '')
      const cleanOg = (f.originalName || '').replace(/^['"]|['"]$/g, '')
      return cleanName === activeFont || cleanOg === activeFont
  })
  if (knownFont) return knownFont.label
  
  // 尝试在映射表中直接查找
  if (fontNameMap[activeFont]) return fontNameMap[activeFont]

  return activeFont
})

const setFont = (fontItem) => {
  if (fontItem && fontItem.value) {
    props.editor.chain().focus().setFontFamily(fontItem.value).run()
    addToRecent(fontItem)
  }
  showFontMenu.value = false
}

const currentColor = computed(() => {
    if (!props.editor) return '#000000'
    const colorAttr = props.editor.getAttributes('textStyle').color
    if (colorAttr) return colorAttr

    // 计算属性 fallback
    if (props.editor.view) {
        try {
            const { from } = props.editor.state.selection
            const dom = props.editor.view.domAtPos(from).node
            const element = dom.nodeType === 3 ? dom.parentElement : dom
            if (element) {
                const rgb = window.getComputedStyle(element).color
                // rgb(0, 0, 0) -> #000000
                if (rgb.startsWith('rgb')) {
                    const [r, g, b] = rgb.match(/\d+/g).map(Number)
                    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)
                }
            }
        } catch(e) {}
    }
    return '#000000'
})

const colorInput = ref(null)
const setColor = (event) => {
  const color = event.target.value
  props.editor.chain().focus().setColor(color).run()
}

const addToRecent = (fontItem) => {
  if (!fontItem || !fontItem.value) return
  
  // 移除已存在的同名字体
  const newList = recentFonts.value.filter(f => f.value !== fontItem.value)
  
  // 添加到头部
  newList.unshift(fontItem)
  
  // 只保留最近 5 个
  if (newList.length > 5) {
    newList.pop()
  }
  
  recentFonts.value = newList
  localStorage.setItem('recent_fonts', JSON.stringify(newList))
}

/* 字号功能相关 */
const showSizeMenu = ref(false)
const currentSizeInput = ref('10.5')

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

const currentFontSizePt = computed(() => {
    if (!props.editor) return 10.5
    
    // 尝试获取 style
    const sizeAttr = props.editor.getAttributes('textStyle').fontSize
    if (sizeAttr) {
        return parseFloat(sizeAttr)
    }
    
    // 如果没有 inline style，尝试通过 window.getComputedStyle 获取当前光标位置的实际字号
    if (props.editor.view) {
        try {
            // 获取当前选区的DOM节点
            const { from } = props.editor.state.selection
            const dom = props.editor.view.domAtPos(from).node
            
            // 如果节点是文本节点，取其父元素
            const element = dom.nodeType === 3 ? dom.parentElement : dom
            
            if (element) {
                const computed = window.getComputedStyle(element).fontSize
                if (computed && computed.endsWith('px')) {
                    // px to pt conversion (1px = 0.75pt)
                    const px = parseFloat(computed)
                    // Round to nearest 0.5
                    return Math.round((px * 0.75) * 2) / 2
                }
            }
        } catch(e) {
            // console.warn('Failed to get computed font size', e)
        }
    }

    return 10.5
})

watch(() => currentFontSizePt.value, (newVal) => {
    // 避免在用户输入时覆盖
    const inputEl = document.activeElement
    if (!inputEl || !inputEl.classList.contains('font-size-input')) {
         currentSizeInput.value = newVal ? newVal.toString() : '10.5'
    }
})

const setSize = (pt) => {
    if (!props.editor) return
    props.editor.chain().focus().setFontSize(pt + 'pt').run()
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
       // 无效输入，重置
       currentSizeInput.value = currentFontSizePt.value.toString()
   }
   // 使输入框失去焦点
   if (document.activeElement && document.activeElement.tagName === 'INPUT') {
       document.activeElement.blur()
   }
}

const fonts = [] // 兼容保留

/* 样式功能相关 */
const showStyleMenu = ref(false)

// 默认样式列表 - 如果父组件没有传入，使用默认值
const defaultStyles = [
    { id: 'paragraph', label: '正文', element: 'p', style: { fontSize: 16, color: '#374151', bold: false } },
    { id: 'heading1', label: '标题 1', element: 'h1', level: 1, style: { fontSize: 32, color: '#111827', bold: true } },
    { id: 'heading2', label: '标题 2', element: 'h2', level: 2, style: { fontSize: 24, color: '#1f2937', bold: true } },
    { id: 'heading3', label: '标题 3', element: 'h3', level: 3, style: { fontSize: 18.72, color: '#374151', bold: true } },
    { id: 'heading4', label: '标题 4', element: 'h4', level: 4, style: { fontSize: 16, color: '#374151', bold: true } },
]

const availableStyles = computed(() => {
    return props.styles && props.styles.length > 0 ? props.styles : defaultStyles
})

const currentStyleLabel = computed(() => {
    if (!props.editor) return '正文'
    
    if (props.editor.isActive('heading', { level: 1 })) return '标题 1'
    if (props.editor.isActive('heading', { level: 2 })) return '标题 2'
    if (props.editor.isActive('heading', { level: 3 })) return '标题 3'
    if (props.editor.isActive('heading', { level: 4 })) return '标题 4'
    
    return '正文'
})

const applyStyle = (styleItem) => {
    if (!props.editor) return
    
    if (styleItem.element === 'p') {
        props.editor.chain().focus().setParagraph().run()
    } else if (styleItem.element.startsWith('h')) {
        props.editor.chain().focus().toggleHeading({ level: styleItem.level }).run()
    }
    
    showStyleMenu.value = false
}

const editStyle = (styleItem, event) => {
    if (event) event.stopPropagation()
    showStyleMenu.value = false
    emit('edit-style', styleItem)
}

// Helper to convert style object to CSS string for preview
const getPreviewStyle = (styleObj) => {
    const s = styleObj.style || {}
    return {
        fontSize: s.fontSize + 'px',
        fontWeight: s.bold ? 'bold' : 'normal',
        fontStyle: s.italic ? 'italic' : 'normal',
        color: s.color,
        fontFamily: s.fontFamily || 'inherit',
        // Reset margins for the dropdown item to avoid layout issues
        margin: 0
    }
}

const triggerImageUpload = () => {
  showImageMenu.value = false
  imageInput.value?.click()
}

const handleImageFile = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  try {
    const url = await uploadImage(file)
    props.editor.chain().focus().setImage({ src: url }).run()
    toast.success('图片上传成功')
  } catch (e) {
    toast.error('图片上传失败: ' + (e.message || '未知错误'))
  } finally {
    event.target.value = '' // reset input
  }
}

const showUrlInput = () => {
  imageMenuStep.value = 'url'
  imageUrlInput.value = ''
  setTimeout(() => {
    if (urlInputRef.value) {
      urlInputRef.value.focus()
    }
  }, 50)
}

const confirmImageUrl = () => {
  if (imageUrlInput.value) {
    props.editor.chain().focus().setImage({ src: imageUrlInput.value }).run()
  }
  showImageMenu.value = false
  imageMenuStep.value = 'list'
}

const cancelUrlInput = () => {
  imageMenuStep.value = 'list'
  imageUrlInput.value = ''
}

watch(showImageMenu, (val) => {
  if (!val) {
    imageMenuStep.value = 'list'
    imageUrlInput.value = ''
  }
})

const insertTable = () => {
  props.editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
}

// 需要后端支持的功能
const handleAIGenerate = () => {
  toast.warning('AI 生成功能需要后端支持')
}

const handleAIOptimize = () => {
  toast.warning('AI 优化功能需要后端支持')
}

const handleInsertChart = () => {
  toast.warning('图表生成功能需要后端支持')
}
</script>

<style scoped>
.toolbar-btn {
  @apply p-2 text-gray-600 hover:bg-gray-200 rounded transition-colors;
}

.toolbar-btn.is-active {
  @apply bg-blue-100 text-blue-600;
}

.toolbar-btn:disabled {
  @apply opacity-40 cursor-not-allowed hover:bg-transparent;
}

.toolbar-btn-ai {
  @apply p-2 text-purple-600 hover:bg-purple-100 rounded transition-colors;
}
</style>
