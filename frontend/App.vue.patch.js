/**
 * App.vue 工作区功能补丁
 * 
 * 使用说明：
 * 1. 备份原 App.vue 文件
 * 2. 按照下面的说明手动修改 App.vue
 * 3. 或者使用提供的完整模板替换
 */

// ============ 需要添加的导入 ============
const newImports = `
import WorkspacePanel from './components/WorkspacePanel.vue'
import { createWorkspaceService } from './services/workspace'
import { FolderOpen } from 'lucide-vue-next'  // 添加到现有的图标导入中
`

// ============ 需要添加的状态变量 ============
const newStateVariables = `
// 工作区管理
const showWorkspacePanel = ref(true)
const activeLeftTab = ref('workspace')  // 'workspace' | 'materials'
const workspaceDocuments = ref([])
const activeDocumentId = ref(null)
let workspaceService = null
let autoSaveInterval = null
`

// ============ 需要添加的工作区管理函数 ============
const workspaceFunctions = `
// 工作区文档管理
const handleSelectDocument = (doc) => {
  // 保存当前文档
  if (activeDocumentId.value && workspaceService) {
    const currentContent = editor.value?.getJSON()
    if (currentContent) {
      workspaceService.saveDocument(activeDocumentId.value, currentContent)
    }
  }

  // 切换到新文档
  activeDocumentId.value = doc.id
  editor.value?.commands.setContent(doc.content)
  toast.success(\`已切换到: \${doc.name}\`)
}

const handleCreateDocument = () => {
  if (!workspaceService) return

  const newDoc = workspaceService.createDocument('未命名文档')
  workspaceDocuments.value = workspaceService.getAllDocuments()
  activeDocumentId.value = newDoc.id
  editor.value?.commands.setContent(newDoc.content)
  toast.success('已创建新文档')
}

const handleRenameDocument = (docId, newName) => {
  if (!workspaceService) return

  try {
    workspaceService.renameDocument(docId, newName)
    workspaceDocuments.value = workspaceService.getAllDocuments()
    toast.success('重命名成功')
  } catch (error) {
    toast.error(error.message)
  }
}

const handleDeleteDocument = (docId) => {
  if (!workspaceService) return

  workspaceService.deleteDocument(docId)
  workspaceDocuments.value = workspaceService.getAllDocuments()

  // 如果删除的是当前文档，切换到第一个文档或创建新文档
  if (activeDocumentId.value === docId) {
    if (workspaceDocuments.value.length > 0) {
      handleSelectDocument(workspaceDocuments.value[0])
    } else {
      handleCreateDocument()
    }
  }

  toast.success('文档已删除')
}

const handleSaveAsNewDocument = (content) => {
  if (!workspaceService) return

  const newDoc = workspaceService.createDocumentFromAIReply(content, 'AI生成')
  workspaceDocuments.value = workspaceService.getAllDocuments()
  toast.success(\`已创建新文档: \${newDoc.name}\`)
}

// 定期自动保存当前文档
const startAutoSave = () => {
  if (autoSaveInterval) {
    clearInterval(autoSaveInterval)
  }

  autoSaveInterval = setInterval(() => {
    if (activeDocumentId.value && workspaceService && editor.value) {
      const content = editor.value.getJSON()
      workspaceService.saveDocument(activeDocumentId.value, content)
      workspaceDocuments.value = workspaceService.getAllDocuments()
    }
  }, 30000) // 每30秒自动保存
}

// 监听编辑器内容变化，标记文档为未保存
watch(() => editor.value?.getJSON(), (newContent) => {
  if (activeDocumentId.value && workspaceService && newContent) {
    workspaceService.markAsUnsaved(activeDocumentId.value)
    workspaceDocuments.value = workspaceService.getAllDocuments()
  }
}, { deep: true })
`

// ============ 修改说明 ============
console.log(`
╔════════════════════════════════════════════════════════════════╗
║                  App.vue 工作区功能集成指南                      ║
╚════════════════════════════════════════════════════════════════╝

请按照以下步骤修改 frontend/src/App.vue：

1. 【导入部分】在 <script setup> 的导入区域添加：
   ${newImports}

2. 【状态变量】在 UI状态 部分添加：
   ${newStateVariables}

3. 【工作区函数】在函数定义区域添加：
   ${workspaceFunctions}

4. 【模板修改】替换左侧边栏的 MaterialPanel 部分为：
   参见 frontend/工作区功能集成说明.md 中的"修改3"

5. 【ChatPanel事件】在 ChatPanel 组件上添加：
   @save-as-new-doc="handleSaveAsNewDocument"

6. 【项目选择】修改 handleSelectProject 函数：
   参见 frontend/工作区功能集成说明.md 中的"修改6"

7. 【返回项目】修改 handleBackToProjects 函数：
   参见 frontend/工作区功能集成说明.md 中的"修改7"

8. 【清理函数】修改 onBeforeUnmount：
   参见 frontend/工作区功能集成说明.md 中的"修改8"

详细说明请查看：frontend/工作区功能集成说明.md

╔════════════════════════════════════════════════════════════════╗
║  提示：建议先备份原文件，然后按照说明逐步修改                    ║
╚════════════════════════════════════════════════════════════════╝
`)

module.exports = {
  newImports,
  newStateVariables,
  workspaceFunctions
}
