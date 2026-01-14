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
import { 
  Undo, Redo,
  Bold, Italic, Underline as UnderlineIcon, Strikethrough, Code,
  Heading1, Heading2, Heading3,
  List, ListOrdered, Quote, FileCode,
  Image as ImageIcon, Table as TableIcon, Minus,
  Sparkles, Wand2, BarChart3
} from 'lucide-vue-next'
import { useToast } from '../composables/useToast'

const props = defineProps({
  editor: {
    type: Object,
    required: true
  }
})

const toast = useToast()

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
