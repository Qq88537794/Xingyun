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
    
    <!-- 标题 -->
    <div class="flex items-center space-x-1 border-r border-gray-300 pr-2 mr-1">
      <button 
        @click="editor.chain().focus().toggleHeading({ level: 1 }).run()"
        :class="{ 'is-active': editor.isActive('heading', { level: 1 }) }"
        class="toolbar-btn"
        title="标题1"
      >
        <Heading1 :size="16" />
      </button>
      <button 
        @click="editor.chain().focus().toggleHeading({ level: 2 }).run()"
        :class="{ 'is-active': editor.isActive('heading', { level: 2 }) }"
        class="toolbar-btn"
        title="标题2"
      >
        <Heading2 :size="16" />
      </button>
      <button 
        @click="editor.chain().focus().toggleHeading({ level: 3 }).run()"
        :class="{ 'is-active': editor.isActive('heading', { level: 3 }) }"
        class="toolbar-btn"
        title="标题3"
      >
        <Heading3 :size="16" />
      </button>
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
      <button 
        @click="insertImage"
        class="toolbar-btn"
        title="插入图片"
      >
        <ImageIcon :size="16" />
      </button>
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
import { ref, computed, onMounted } from 'vue'
import { 
  Undo, Redo,
  Bold, Italic, Underline as UnderlineIcon, Strikethrough, Code,
  Heading1, Heading2, Heading3,
  List, ListOrdered, Quote, FileCode,
  Image as ImageIcon, Table as TableIcon, Minus,
  Sparkles, Wand2, BarChart3,
  Type, ChevronDown
} from 'lucide-vue-next'
import { useToast } from '../composables/useToast'

const props = defineProps({
  editor: {
    type: Object,
    required: true
  }
})

const toast = useToast()
const showFontMenu = ref(false)
const systemFonts = ref([])
const recentFonts = ref([])

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

  // 加载系统字体
  if (window.electronAPI && window.electronAPI.getSystemFonts) {
    try {
      const fonts = await window.electronAPI.getSystemFonts()
      
      // 过滤和处理字体
      const processedFonts = fonts
        .filter(f => !f.startsWith('@')) // 过滤掉 Windows 的竖排字体
        .filter(f => !['Webdings', 'Wingdings', 'Wingdings 2', 'Wingdings 3', 'Marlett', 'Symbol'].includes(f)) // 过滤符号字体
        .map(f => {
          // 尝试本地化名称
          const cleanName = f.replace(/^"|"$/g, '')
          const displayName = fontNameMap[cleanName] || cleanName
          return {
            label: displayName,
            value: `"${cleanName}"`, // 加引号以防止空格问题
            originalName: cleanName,
            // 标记类型用于排序：优先字体 > 中文(有映射) > 其他英文
            isPriority: priorityFonts.includes(cleanName),
            isChinese: !!fontNameMap[cleanName]
          }
        })
      
      // 排序：优先字体 -> 其他中文 -> 英文(A-Z)
      processedFonts.sort((a, b) => {
        if (a.isPriority && !b.isPriority) return -1
        if (!a.isPriority && b.isPriority) return 1
        
        if (a.isChinese && !b.isChinese) return -1
        if (!a.isChinese && b.isChinese) return 1
        
        return a.label.localeCompare(b.label)
      })

      systemFonts.value = processedFonts
    } catch (e) {
      console.error('Failed to load system fonts:', e)
      // 降级使用硬编码列表
      systemFonts.value = rawSystemFonts
    }
  } else {
    // 浏览器环境 fallback
    systemFonts.value = rawSystemFonts
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

// 排序后的系统字体列表
const sortedSystemFonts = computed(() => {
  // 如果有最近使用的字体，过滤掉它们以避免重复？
  // 或者保留重复，但最近使用在顶部更方便。这里不做过滤。
  return systemFonts.value
})

const currentFontLabel = computed(() => {
  if (!props.editor) return '微软雅黑'
  
  // 获取当前光标或选区的字体属性
  let activeFont = props.editor.getAttributes('textStyle').fontFamily
  
  if (!activeFont) return '微软雅黑' // 默认显示微软雅黑
  
  // 清理引号
  activeFont = activeFont.replace(/^"|"$/g, '').split(',')[0].trim()
  
  // 在已加载的系统字体中查找
  const knownFont = systemFonts.value.find(f => f.originalName === activeFont)
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

const fonts = [] // 兼容保留

const insertImage = () => {
  const url = prompt('请输入图片URL:')
  if (url) {
    props.editor.chain().focus().setImage({ src: url }).run()
  }
}

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
