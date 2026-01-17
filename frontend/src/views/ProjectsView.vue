<template>
  <!-- 未登录状态 - 显示登录注册界面 -->
  <div v-if="!authStore.isAuthenticated" class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
    <div class="w-full max-w-md mx-4">
      <!-- 登录界面 -->
      <div v-if="authView === 'login'" class="bg-white rounded-2xl shadow-2xl p-8">
        <div class="text-center mb-8">
          <div class="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4">
            <FileText :size="32" class="text-white" />
          </div>
          <h1 class="text-2xl font-bold text-gray-900">行云文档</h1>
          <p class="text-gray-600 mt-2">登录您的账户</p>
        </div>

        <form @submit.prevent="handleLogin">
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">用户名</label>
              <input
                v-model="loginForm.username"
                type="text"
                required
                placeholder="请输入用户名"
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">密码</label>
              <input
                v-model="loginForm.password"
                type="password"
                required
                placeholder="请输入密码"
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              />
            </div>
          </div>

          <button
            type="submit"
            :disabled="submitting"
            class="w-full mt-6 px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center"
          >
            <Loader2 v-if="submitting" :size="18" class="animate-spin mr-2" />
            登录
          </button>
        </form>

        <div class="mt-6 text-center">
          <button
            @click="authView = 'register'"
            class="text-sm text-blue-600 hover:text-blue-700"
          >
            还没有账户？立即注册
          </button>
        </div>
      </div>

      <!-- 注册界面 -->
      <div v-else class="bg-white rounded-2xl shadow-2xl p-8">
        <div class="text-center mb-8">
          <div class="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4">
            <FileText :size="32" class="text-white" />
          </div>
          <h1 class="text-2xl font-bold text-gray-900">行云文档</h1>
          <p class="text-gray-600 mt-2">创建新账户</p>
        </div>

        <form @submit.prevent="handleRegister">
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">用户名</label>
              <input
                v-model="registerForm.username"
                type="text"
                required
                placeholder="请输入用户名"
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">邮箱</label>
              <input
                v-model="registerForm.email"
                type="email"
                required
                placeholder="请输入邮箱"
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">密码</label>
              <input
                v-model="registerForm.password"
                type="password"
                required
                placeholder="请输入密码"
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              />
            </div>
          </div>

          <button
            type="submit"
            :disabled="submitting"
            class="w-full mt-6 px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center"
          >
            <Loader2 v-if="submitting" :size="18" class="animate-spin mr-2" />
            注册
          </button>
        </form>

        <div class="mt-6 text-center">
          <button
            @click="authView = 'login'"
            class="text-sm text-blue-600 hover:text-blue-700"
          >
            已有账户？立即登录
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- 已登录状态 - 显示桌面和文件夹 -->
  <div v-else class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex">
    <!-- 左侧文件夹侧边栏 -->
    <div class="w-64 bg-white shadow-lg flex flex-col">
      <!-- 侧边栏头部 -->
      <div class="p-4 border-b border-gray-200">
        <div class="flex items-center space-x-3 mb-4">
          <div class="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
            <FileText :size="20" class="text-white" />
          </div>
          <h1 class="text-lg font-bold text-gray-900">行云文档</h1>
        </div>
        
        <button 
          @click="showCreateFolderModal = true"
          class="w-full px-3 py-2 bg-blue-50 text-blue-600 rounded-lg font-medium hover:bg-blue-100 transition-colors flex items-center justify-center space-x-2 text-sm"
        >
          <FolderPlus :size="16" />
          <span>新建文件夹</span>
        </button>
      </div>

      <!-- 文件夹列表 -->
      <div class="flex-1 overflow-y-auto p-3">
        <!-- 所有项目 -->
        <button
          @click="showAllProjects"
          @dragover.prevent="handleDragOverDesktop"
          @dragleave="handleDragLeaveDesktop"
          @drop.prevent="handleDropToDesktop"
          :class="[
            'w-full px-3 py-2 rounded-lg flex items-center space-x-3 mb-2 transition-colors',
            !selectedFolder ? 'bg-blue-100 text-blue-700' : 'text-gray-700 hover:bg-gray-100',
            dragOverDesktop ? 'ring-2 ring-blue-400 bg-blue-50' : ''
          ]"
        >
          <FolderOpen :size="18" />
          <span class="font-medium">桌面</span>
          <span class="ml-auto text-xs bg-gray-200 px-2 py-1 rounded-full">
            {{ projects.filter(p => !p.folder_id).length }}
          </span>
        </button>

        <!-- 文件夹列表 -->
        <div v-for="folder in folders" :key="folder.id" class="mb-1">
          <button
            @click="selectFolder(folder)"
            @dragover.prevent="handleDragOver($event, folder)"
            @dragleave="handleDragLeave($event, folder)"
            @drop.prevent="handleDrop($event, folder)"
            :class="[
              'w-full px-3 py-2 rounded-lg flex items-center space-x-3 transition-colors group',
              selectedFolder?.id === folder.id ? 'bg-blue-100 text-blue-700' : 'text-gray-700 hover:bg-gray-100',
              dragOverFolder?.id === folder.id ? 'ring-2 ring-blue-400 bg-blue-50' : ''
            ]"
          >
            <Folder :size="18" :class="`text-${folder.color}-500`" />
            <span class="flex-1 text-left font-medium truncate">{{ folder.name }}</span>
            <span class="text-xs bg-gray-200 px-2 py-1 rounded-full">
              {{ projects.filter(p => p.folder_id === folder.id).length }}
            </span>
            
            <!-- 文件夹操作按钮 -->
            <div class="opacity-0 group-hover:opacity-100 flex items-center space-x-1">
              <button
                @click.stop="openEditFolderModal(folder)"
                class="p-1 hover:bg-white rounded"
                title="编辑"
              >
                <Edit2 :size="14" />
              </button>
              <button
                @click.stop="confirmDeleteFolder(folder)"
                class="p-1 hover:bg-white rounded text-red-500"
                title="删除"
              >
                <Trash2 :size="14" />
              </button>
            </div>
          </button>
        </div>
      </div>

      <!-- 用户信息 -->
      <div class="p-4 border-t border-gray-200">
        <button
          @click="openUserProfileModal"
          class="w-full flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <div class="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center overflow-hidden">
            <img 
              v-if="authStore.user?.avatar" 
              :src="`http://localhost:5000${authStore.user.avatar}`" 
              :alt="authStore.user?.username"
              class="w-full h-full object-cover"
            />
            <span v-else class="text-white font-medium text-lg">
              {{ authStore.user?.username?.charAt(0).toUpperCase() }}
            </span>
          </div>
          <div class="flex-1 text-left">
            <div class="text-sm font-medium text-gray-900">{{ authStore.user?.username }}</div>
            <div class="text-xs text-gray-500">{{ authStore.user?.email }}</div>
          </div>
          <ChevronDown :size="16" class="text-gray-400" />
        </button>
      </div>
    </div>

    <!-- 右侧主内容区 -->
    <div class="flex-1 flex flex-col">
      <!-- 顶部操作栏 -->
      <div class="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-bold text-gray-900">
              {{ selectedFolder ? selectedFolder.name : '桌面' }}
            </h2>
            <p class="text-sm text-gray-600 mt-1">
              {{ displayedProjects.length }} 个项目
            </p>
          </div>
          <button 
            @click="showCreateModal = true"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <Plus :size="18" />
            <span>新建项目</span>
          </button>
        </div>
      </div>

      <!-- 项目内容区 -->
      <div class="flex-1 overflow-y-auto p-6">
        <!-- 加载状态 -->
        <div v-if="loading" class="flex items-center justify-center py-20">
          <Loader2 :size="32" class="animate-spin text-blue-600" />
          <span class="ml-3 text-gray-600">加载中...</span>
        </div>

        <!-- 空状态 -->
        <div v-else-if="displayedProjects.length === 0" class="text-center py-20">
          <div class="inline-flex items-center justify-center w-20 h-20 bg-gray-100 rounded-full mb-4">
            <FolderOpen :size="40" class="text-gray-400" />
          </div>
          <h3 class="text-lg font-medium text-gray-900 mb-2">
            {{ selectedFolder ? '文件夹为空' : '桌面为空' }}
          </h3>
          <p class="text-gray-500 mb-6">
            {{ selectedFolder ? '将项目拖拽到此文件夹' : '创建您的第一个项目，开始智能文档编辑' }}
          </p>
          <button 
            v-if="!selectedFolder"
            @click="showCreateModal = true"
            class="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            创建第一个项目
          </button>
        </div>

        <!-- 项目网格 -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div 
            v-for="project in displayedProjects" 
            :key="project.id"
            draggable="true"
            @dragstart="handleDragStart($event, project)"
            @dragend="handleDragEnd"
            class="bg-white rounded-2xl shadow-md hover:shadow-lg transition-shadow cursor-pointer group"
            @click="selectProject(project)"
          >
            <div class="p-6">
              <div class="flex items-start justify-between mb-4">
                <div class="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                  <Folder :size="24" class="text-blue-600" />
                </div>
                <div class="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button 
                    v-if="folders.length > 0"
                    @click.stop="openMoveToFolderModal(project)"
                    class="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                    title="移动到文件夹"
                  >
                    <MoveRight :size="16" />
                  </button>
                  <button 
                    @click.stop="openEditModal(project)"
                    class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    title="编辑"
                  >
                    <Edit2 :size="16" />
                  </button>
                  <button 
                    @click.stop="confirmDelete(project)"
                    class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="删除"
                  >
                    <Trash2 :size="16" />
                  </button>
                </div>
              </div>
              
              <h3 class="text-lg font-semibold text-gray-900 mb-2 truncate">{{ project.name }}</h3>
              <p class="text-sm text-gray-500 line-clamp-2 mb-4">
                {{ project.description || '暂无描述' }}
              </p>
              
              <div class="flex items-center justify-between text-xs text-gray-400">
                <span>{{ formatDate(project.created_at) }}</span>
                <span :class="project.status === 'active' ? 'text-green-500' : 'text-gray-400'">
                  {{ project.status === 'active' ? '活跃' : '已归档' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑项目弹窗 -->
    <div v-if="showCreateModal || showEditModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-bold text-gray-900">
            {{ showEditModal ? '编辑项目' : '新建项目' }}
          </h3>
          <button 
            @click="closeModals"
            class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X :size="20" />
          </button>
        </div>

        <form @submit.prevent="showEditModal ? handleUpdate() : handleCreate()">
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">项目名称</label>
              <input
                v-model="formData.name"
                type="text"
                required
                placeholder="输入项目名称"
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">项目描述（可选）</label>
              <textarea
                v-model="formData.description"
                rows="3"
                placeholder="简单描述一下这个项目..."
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition resize-none"
              ></textarea>
            </div>

            <div v-if="folders.length > 0">
              <label class="block text-sm font-medium text-gray-700 mb-2">所属文件夹（可选）</label>
              <select
                v-model="formData.folder_id"
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              >
                <option :value="null">无（根目录）</option>
                <option v-for="folder in folders" :key="folder.id" :value="folder.id">
                  {{ folder.name }}
                </option>
              </select>
            </div>
          </div>

          <div class="flex space-x-3 mt-6">
            <button
              type="button"
              @click="closeModals"
              class="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="submitting"
              class="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center"
            >
              <Loader2 v-if="submitting" :size="18" class="animate-spin mr-2" />
              {{ showEditModal ? '保存' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 删除项目确认弹窗 -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 p-6">
        <div class="text-center">
          <div class="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
            <AlertTriangle :size="32" class="text-red-600" />
          </div>
          <h3 class="text-lg font-bold text-gray-900 mb-2">确认删除</h3>
          <p class="text-gray-600 mb-6">
            确定要删除项目 "<span class="font-medium">{{ deleteTarget?.name }}</span>" 吗？此操作不可恢复。
          </p>
          
          <div class="flex space-x-3">
            <button
              @click="showDeleteModal = false"
              class="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
            <button
              @click="handleDelete"
              :disabled="submitting"
              class="flex-1 px-4 py-3 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center justify-center"
            >
              <Loader2 v-if="submitting" :size="18" class="animate-spin mr-2" />
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 移动到文件夹弹窗 -->
    <div v-if="showMoveToFolderModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-bold text-gray-900">移动到文件夹</h3>
          <button 
            @click="showMoveToFolderModal = false"
            class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X :size="20" />
          </button>
        </div>

        <div class="space-y-2 max-h-96 overflow-y-auto">
          <!-- 移到根目录 -->
          <button
            v-if="moveTarget?.folder_id"
            @click="handleMoveToFolder(null)"
            class="w-full px-4 py-3 text-left rounded-lg hover:bg-gray-100 transition-colors flex items-center space-x-3"
          >
            <FolderOpen :size="20" class="text-gray-500" />
            <span class="font-medium">根目录（无文件夹）</span>
          </button>

          <!-- 文件夹列表 -->
          <button
            v-for="folder in folders.filter(f => f.id !== moveTarget?.folder_id)"
            :key="folder.id"
            @click="handleMoveToFolder(folder.id)"
            class="w-full px-4 py-3 text-left rounded-lg hover:bg-blue-50 transition-colors flex items-center space-x-3"
          >
            <Folder :size="20" :class="`text-${folder.color}-500`" />
            <span class="font-medium">{{ folder.name }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 创建/编辑文件夹弹窗 -->
    <div v-if="showCreateFolderModal || showEditFolderModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-bold text-gray-900">
            {{ showEditFolderModal ? '编辑文件夹' : '新建文件夹' }}
          </h3>
          <button 
            @click="closeFolderModals"
            class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X :size="20" />
          </button>
        </div>

        <form @submit.prevent="showEditFolderModal ? handleUpdateFolder() : handleCreateFolder()">
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">文件夹名称</label>
              <input
                v-model="folderFormData.name"
                type="text"
                required
                placeholder="输入文件夹名称"
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              />
            </div>
          </div>

          <div class="flex space-x-3 mt-6">
            <button
              type="button"
              @click="closeFolderModals"
              class="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="submitting"
              class="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center"
            >
              <Loader2 v-if="submitting" :size="18" class="animate-spin mr-2" />
              {{ showEditFolderModal ? '保存' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 删除文件夹确认弹窗 -->
    <div v-if="showDeleteFolderModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 p-6">
        <div class="text-center">
          <div class="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
            <AlertTriangle :size="32" class="text-red-600" />
          </div>
          <h3 class="text-lg font-bold text-gray-900 mb-2">确认删除</h3>
          <p class="text-gray-600 mb-6">
            确定要删除文件夹 "<span class="font-medium">{{ deleteFolderTarget?.name }}</span>" 吗？<br>
            <span class="text-sm">文件夹内的项目将移到根目录。</span>
          </p>
          
          <div class="flex space-x-3">
            <button
              @click="showDeleteFolderModal = false"
              class="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
            <button
              @click="handleDeleteFolder"
              :disabled="submitting"
              class="flex-1 px-4 py-3 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center justify-center"
            >
              <Loader2 v-if="submitting" :size="18" class="animate-spin mr-2" />
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 用户个人资料弹窗 -->
    <div v-if="showUserProfileModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-bold text-gray-900">个人资料</h3>
          <button 
            @click="closeUserProfileModal"
            class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X :size="20" />
          </button>
        </div>

        <div class="space-y-6">
          <!-- 用户头像 -->
          <div class="flex flex-col items-center">
            <div class="relative group">
              <div class="w-24 h-24 bg-blue-600 rounded-full flex items-center justify-center cursor-pointer group-hover:opacity-80 transition-opacity overflow-hidden">
                <img 
                  v-if="authStore.user?.avatar" 
                  :src="`http://localhost:5000${authStore.user.avatar}`" 
                  :alt="authStore.user?.username"
                  class="w-full h-full object-cover"
                />
                <span v-else class="text-white font-bold text-4xl">
                  {{ authStore.user?.username?.charAt(0).toUpperCase() }}
                </span>
              </div>
              <button
                @click="handleChangeAvatar"
                class="absolute bottom-0 right-0 w-8 h-8 bg-white rounded-full shadow-lg flex items-center justify-center hover:bg-gray-100 transition-colors"
                title="更换头像"
              >
                <Camera :size="16" class="text-gray-600" />
              </button>
            </div>
            <p class="text-xs text-gray-500 mt-2">点击相机图标更换头像</p>
          </div>

          <!-- 编辑表单 -->
          <form @submit.prevent="handleUpdateProfile">
            <div class="space-y-4">
              <!-- 用户名 -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">用户名</label>
                <input
                  v-model="profileForm.username"
                  type="text"
                  :disabled="!isEditingProfile"
                  :class="[
                    'w-full px-4 py-3 border rounded-lg transition',
                    isEditingProfile 
                      ? 'border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none' 
                      : 'bg-gray-50 border-gray-200 text-gray-900 cursor-not-allowed'
                  ]"
                />
              </div>
              
              <!-- 邮箱 -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">邮箱</label>
                <input
                  v-model="profileForm.email"
                  type="email"
                  :disabled="!isEditingProfile"
                  :class="[
                    'w-full px-4 py-3 border rounded-lg transition',
                    isEditingProfile 
                      ? 'border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none' 
                      : 'bg-gray-50 border-gray-200 text-gray-900 cursor-not-allowed'
                  ]"
                />
              </div>

              <!-- 修改密码区域 -->
              <div v-if="isEditingProfile" class="pt-4 border-t border-gray-200">
                <div class="flex items-center justify-between mb-4">
                  <label class="text-sm font-medium text-gray-700">修改密码</label>
                  <button
                    type="button"
                    @click="togglePasswordFields"
                    class="text-sm text-blue-600 hover:text-blue-700"
                  >
                    {{ showPasswordFields ? '取消修改' : '修改密码' }}
                  </button>
                </div>

                <div v-if="showPasswordFields" class="space-y-3">
                  <!-- 步骤1: 验证当前密码 -->
                  <div v-if="passwordStep === 1">
                    <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                      <p class="text-xs text-blue-700">步骤 1/2: 请先输入当前密码进行验证</p>
                    </div>
                    <div>
                      <label class="block text-xs font-medium text-gray-600 mb-1">当前密码</label>
                      <input
                        v-model="profileForm.currentPassword"
                        type="password"
                        placeholder="请输入当前密码"
                        @keyup.enter="verifyCurrentPassword"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
                      />
                    </div>
                    <button
                      type="button"
                      @click="verifyCurrentPassword"
                      :disabled="!profileForm.currentPassword || verifyingPassword"
                      class="w-full mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                      <Loader2 v-if="verifyingPassword" :size="16" class="animate-spin mr-2" />
                      {{ verifyingPassword ? '验证中...' : '验证密码' }}
                    </button>
                  </div>

                  <!-- 步骤2: 输入新密码 -->
                  <div v-if="passwordStep === 2">
                    <div class="bg-green-50 border border-green-200 rounded-lg p-3 mb-3">
                      <p class="text-xs text-green-700">✓ 当前密码验证成功！步骤 2/2: 请设置新密码</p>
                    </div>
                    <div>
                      <label class="block text-xs font-medium text-gray-600 mb-1">新密码</label>
                      <input
                        v-model="profileForm.newPassword"
                        type="password"
                        placeholder="请输入新密码（至少6个字符）"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
                      />
                    </div>
                    <div>
                      <label class="block text-xs font-medium text-gray-600 mb-1">确认新密码</label>
                      <input
                        v-model="profileForm.confirmPassword"
                        type="password"
                        placeholder="请再次输入新密码"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="pt-6 border-t border-gray-200 mt-6 space-y-3">
              <div v-if="!isEditingProfile" class="space-y-2">
                <button
                  type="button"
                  @click="startEditingProfile"
                  class="w-full px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
                >
                  编辑资料
                </button>
                <button
                  type="button"
                  @click="handleLogout"
                  class="w-full px-4 py-3 bg-red-50 text-red-600 rounded-lg font-medium hover:bg-red-100 transition-colors flex items-center justify-center space-x-2"
                >
                  <LogOut :size="18" />
                  <span>退出登录</span>
                </button>
              </div>

              <div v-else class="flex space-x-3">
                <button
                  type="button"
                  @click="cancelEditingProfile"
                  class="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  :disabled="submitting"
                  class="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center"
                >
                  <Loader2 v-if="submitting" :size="18" class="animate-spin mr-2" />
                  保存修改
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
  
  <!-- 错误提示模态框 -->
  <ErrorModal
    :show="errorModal.show"
    :type="errorModal.type"
    :title="errorModal.title"
    :message="errorModal.message"
    @close="closeErrorModal"
  />
</template>


<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { FileText, Plus, Folder, FolderOpen, FolderPlus, Edit2, Trash2, X, Loader2, LogOut, AlertTriangle, MoveRight, ChevronDown, Camera } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { getProjects, createProject, updateProject, deleteProject } from '../services/projects'
import { getFolders, createFolder, updateFolder, deleteFolder, addProjectToFolder, removeProjectFromFolder } from '../services/folders'
import { login, register, updateUserProfile } from '../services/auth'
import { useToast } from '../composables/useToast'
import ErrorModal from '../components/ErrorModal.vue'

const emit = defineEmits(['select-project'])

const authStore = useAuthStore()
const toast = useToast()

// 个人资料编辑状态（需要在 watch 之前声明）
const isEditingProfile = ref(false)
const showPasswordFields = ref(false)
const passwordStep = ref(1) // 1: 输入当前密码, 2: 输入新密码
const verifyingPassword = ref(false) // 验证当前密码的加载状态
const profileForm = ref({
  username: '',
  email: '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 监听认证状态变化
watch(() => authStore.isAuthenticated, (newVal) => {
  if (newVal) {
    fetchProjects()
    fetchFolders()
  }
})

// 监听用户信息变化，更新表单数据
watch(() => authStore.user, (newUser) => {
  if (newUser && !isEditingProfile.value) {
    profileForm.value = {
      username: newUser.username || '',
      email: newUser.email || '',
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
  }
}, { immediate: true, deep: true })

// 认证状态
const authView = ref('login') // 'login' | 'register'
const loginForm = ref({
  username: '',
  password: ''
})
const registerForm = ref({
  username: '',
  email: '',
  password: ''
})

// 状态
const projects = ref([])
const folders = ref([])
const loading = ref(true)
const submitting = ref(false)
const selectedFolder = ref(null)
const draggedProject = ref(null)
const dragOverFolder = ref(null)
const dragOverDesktop = ref(false)

// 弹窗状态
const showCreateModal = ref(false)
const showEditModal = ref(false)
const showDeleteModal = ref(false)
const showCreateFolderModal = ref(false)
const showEditFolderModal = ref(false)
const showDeleteFolderModal = ref(false)
const showMoveToFolderModal = ref(false)
const showUserProfileModal = ref(false)
const editTarget = ref(null)

// 错误提示模态框
const errorModal = ref({
  show: false,
  type: 'error',
  title: '',
  message: ''
})

const showError = (message, title = '错误', type = 'error') => {
  errorModal.value = {
    show: true,
    type,
    title,
    message
  }
}

const closeErrorModal = () => {
  errorModal.value.show = false
}
const deleteTarget = ref(null)
const editFolderTarget = ref(null)
const moveTarget = ref(null)
const deleteFolderTarget = ref(null)

// 表单数据
const formData = ref({
  name: '',
  description: '',
  folder_id: null
})

const folderFormData = ref({
  name: '',
  color: 'blue'
})

// 计算当前显示的项目
const displayedProjects = computed(() => {
  if (!selectedFolder.value) {
    return projects.value.filter(p => !p.folder_id)
  }
  return projects.value.filter(p => p.folder_id === selectedFolder.value.id)
})

// 加载项目列表
const fetchProjects = async () => {
  loading.value = true
  try {
    projects.value = await getProjects()
  } catch (err) {
    console.error('获取项目列表失败:', err)
    toast.error('获取项目列表失败')
  } finally {
    loading.value = false
  }
}

// 加载文件夹列表
const fetchFolders = async () => {
  try {
    folders.value = await getFolders()
  } catch (err) {
    console.error('获取文件夹列表失败:', err)
    toast.error('获取文件夹列表失败')
  }
}

// 登录处理
const handleLogin = async () => {
  if (!loginForm.value.username.trim() || !loginForm.value.password.trim()) {
    showError('请输入用户名和密码', '登录失败', 'warning')
    return
  }
  
  submitting.value = true
  try {
    const result = await login(loginForm.value.username, loginForm.value.password)
    
    // 后端返回 access_token，需要统一为 token
    if (!result.access_token || !result.user) {
      throw new Error('登录响应数据格式错误')
    }
    
    // 手动设置用户信息和 token
    authStore.user = result.user
    authStore.token = result.access_token
    localStorage.setItem('token', result.access_token)
    localStorage.setItem('user', JSON.stringify(result.user))
    
    toast.success('登录成功！欢迎回来')
    
    // watch 会自动加载数据，不需要手动调用
  } catch (err) {
    console.error('登录失败:', err)
    
    // 根据不同的错误状态码显示不同的提示
    if (err.response) {
      const status = err.response.status
      const errorMsg = err.response.data?.error
      
      switch (status) {
        case 400:
          showError(errorMsg || '请求参数错误，请检查输入信息', '登录失败')
          break
        case 401:
          showError('用户名或密码错误，请检查后重试\n\n提示：\n• 用户名区分大小写\n• 可以使用邮箱登录', '登录失败')
          break
        case 404:
          showError('该用户不存在，请检查用户名或先注册账号', '登录失败')
          break
        case 500:
          showError('服务器错误，请稍后重试\n如果问题持续存在，请联系管理员', '服务器错误')
          break
        default:
          showError(errorMsg || '登录失败，请重试', '登录失败')
      }
    } else if (err.request) {
      showError('无法连接到服务器\n\n请检查：\n• 网络连接是否正常\n• 后端服务是否启动', '网络错误')
    } else {
      showError(err.message || '登录失败，请重试', '登录失败')
    }
  } finally {
    submitting.value = false
  }
}

// 注册处理
const handleRegister = async () => {
  if (!registerForm.value.username.trim() || !registerForm.value.email.trim() || !registerForm.value.password.trim()) {
    showError('请填写所有必填字段', '注册失败', 'warning')
    return
  }
  
  // 前端验证
  if (registerForm.value.username.length < 2 || registerForm.value.username.length > 64) {
    showError('用户名长度应为 2-64 个字符', '注册失败', 'warning')
    return
  }
  
  if (registerForm.value.password.length < 6) {
    showError('密码长度至少为 6 个字符\n\n建议使用包含字母、数字和特殊字符的强密码', '注册失败', 'warning')
    return
  }
  
  // 简单的邮箱格式验证
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(registerForm.value.email)) {
    showError('请输入有效的邮箱地址\n\n例如：user@example.com', '注册失败', 'warning')
    return
  }
  
  submitting.value = true
  try {
    const result = await register(
      registerForm.value.username,
      registerForm.value.email,
      registerForm.value.password
    )
    
    // 后端返回 access_token，需要统一为 token
    if (!result.access_token || !result.user) {
      throw new Error('注册响应数据格式错误')
    }
    
    // 手动设置用户信息和 token
    authStore.user = result.user
    authStore.token = result.access_token
    localStorage.setItem('token', result.access_token)
    localStorage.setItem('user', JSON.stringify(result.user))
    
    toast.success('注册成功！欢迎使用行云文档')
    
    // watch 会自动加载数据，不需要手动调用
  } catch (err) {
    console.error('注册失败:', err)
    
    // 根据不同的错误状态码显示不同的提示
    if (err.response) {
      const status = err.response.status
      const errorMsg = err.response.data?.error
      
      switch (status) {
        case 400:
          showError(errorMsg || '请求参数错误，请检查输入信息', '注册失败')
          break
        case 409:
          // 冲突错误，用户名或邮箱已存在
          if (errorMsg?.includes('用户名')) {
            showError('该用户名已被注册\n\n请尝试：\n• 更换一个新的用户名\n• 如果是您的账号，请直接登录', '用户名已存在')
          } else if (errorMsg?.includes('邮箱')) {
            showError('该邮箱已被注册\n\n请尝试：\n• 更换一个新的邮箱\n• 如果是您的账号，请直接登录', '邮箱已存在')
          } else {
            showError('用户名或邮箱已被注册\n\n请更换后重试或直接登录', '注册失败')
          }
          break
        case 500:
          showError('服务器错误，请稍后重试\n如果问题持续存在，请联系管理员', '服务器错误')
          break
        default:
          showError(errorMsg || '注册失败，请重试', '注册失败')
      }
    } else if (err.request) {
      showError('无法连接到服务器\n\n请检查：\n• 网络连接是否正常\n• 后端服务是否启动', '网络错误')
    } else {
      showError(err.message || '注册失败，请重试', '注册失败')
    }
  } finally {
    submitting.value = false
  }
}

// 创建项目
const handleCreate = async () => {
  if (!formData.value.name.trim()) {
    toast.warning('请输入项目名称')
    return
  }
  
  submitting.value = true
  try {
    const result = await createProject(formData.value.name, formData.value.description)
    const newProject = result.project
    
    // 如果选择了文件夹，将项目添加到文件夹
    if (formData.value.folder_id) {
      await addProjectToFolder(formData.value.folder_id, newProject.id)
      newProject.folder_id = formData.value.folder_id
    }
    
    projects.value.unshift(newProject)
    toast.success('项目创建成功')
    closeModals()
  } catch (err) {
    console.error('创建项目失败:', err)
    toast.error(err.response?.data?.error || '创建项目失败')
  } finally {
    submitting.value = false
  }
}

// 更新项目
const handleUpdate = async () => {
  if (!formData.value.name.trim()) {
    toast.warning('请输入项目名称')
    return
  }
  
  submitting.value = true
  try {
    // 更新项目基本信息和 folder_id
    const result = await updateProject(editTarget.value.id, {
      name: formData.value.name,
      description: formData.value.description,
      folder_id: formData.value.folder_id
    })
    
    const index = projects.value.findIndex(p => p.id === editTarget.value.id)
    if (index !== -1) {
      projects.value[index] = result.project
    }
    
    toast.success('项目更新成功')
    closeModals()
  } catch (err) {
    console.error('更新项目失败:', err)
    toast.error(err.response?.data?.error || '更新项目失败')
  } finally {
    submitting.value = false
  }
}

// 删除项目
const handleDelete = async () => {
  submitting.value = true
  try {
    await deleteProject(deleteTarget.value.id)
    projects.value = projects.value.filter(p => p.id !== deleteTarget.value.id)
    toast.success('项目删除成功')
    showDeleteModal.value = false
    deleteTarget.value = null
  } catch (err) {
    console.error('删除项目失败:', err)
    toast.error(err.response?.data?.error || '删除项目失败')
  } finally {
    submitting.value = false
  }
}

// 创建文件夹
const handleCreateFolder = async () => {
  if (!folderFormData.value.name.trim()) {
    toast.warning('请输入文件夹名称')
    return
  }
  
  submitting.value = true
  try {
    const result = await createFolder(folderFormData.value.name, folderFormData.value.color)
    folders.value.unshift(result.folder)
    toast.success('文件夹创建成功')
    closeFolderModals()
  } catch (err) {
    console.error('创建文件夹失败:', err)
    toast.error(err.response?.data?.error || '创建文件夹失败')
  } finally {
    submitting.value = false
  }
}

// 更新文件夹
const handleUpdateFolder = async () => {
  if (!folderFormData.value.name.trim()) {
    toast.warning('请输入文件夹名称')
    return
  }
  
  submitting.value = true
  try {
    const result = await updateFolder(editFolderTarget.value.id, folderFormData.value)
    const index = folders.value.findIndex(f => f.id === editFolderTarget.value.id)
    if (index !== -1) {
      folders.value[index] = result.folder
    }
    toast.success('文件夹更新成功')
    closeFolderModals()
  } catch (err) {
    console.error('更新文件夹失败:', err)
    toast.error(err.response?.data?.error || '更新文件夹失败')
  } finally {
    submitting.value = false
  }
}

// 删除文件夹
const handleDeleteFolder = async () => {
  submitting.value = true
  try {
    await deleteFolder(deleteFolderTarget.value.id)
    folders.value = folders.value.filter(f => f.id !== deleteFolderTarget.value.id)
    if (selectedFolder.value?.id === deleteFolderTarget.value.id) {
      selectedFolder.value = null
    }
    toast.success('文件夹删除成功')
    showDeleteFolderModal.value = false
    deleteFolderTarget.value = null
    await fetchProjects()
  } catch (err) {
    console.error('删除文件夹失败:', err)
    toast.error(err.response?.data?.error || '删除文件夹失败')
  } finally {
    submitting.value = false
  }
}

// 选择项目
const selectProject = (project) => {
  emit('select-project', project)
}

// 选择文件夹
const selectFolder = (folder) => {
  selectedFolder.value = folder
}

// 显示所有项目
const showAllProjects = () => {
  selectedFolder.value = null
}

// 打开编辑项目弹窗
const openEditModal = (project) => {
  editTarget.value = project
  formData.value = {
    name: project.name,
    description: project.description || '',
    folder_id: project.folder_id || null
  }
  showEditModal.value = true
}

// 确认删除项目
const confirmDelete = (project) => {
  deleteTarget.value = project
  showDeleteModal.value = true
}

// 打开移动到文件夹弹窗
const openMoveToFolderModal = (project) => {
  moveTarget.value = project
  showMoveToFolderModal.value = true
}

// 处理移动到文件夹
const handleMoveToFolder = async (folderId) => {
  submitting.value = true
  try {
    // 直接更新项目的 folder_id
    await updateProject(moveTarget.value.id, {
      folder_id: folderId
    })
    
    // 更新本地项目数据
    const index = projects.value.findIndex(p => p.id === moveTarget.value.id)
    if (index !== -1) {
      projects.value[index].folder_id = folderId
    }
    
    toast.success(folderId ? '项目已移动到文件夹' : '项目已移到桌面')
    showMoveToFolderModal.value = false
    moveTarget.value = null
  } catch (err) {
    console.error('移动项目失败:', err)
    toast.error(err.response?.data?.error || '移动项目失败')
  } finally {
    submitting.value = false
  }
}

// 拖拽开始
const handleDragStart = (event, project) => {
  draggedProject.value = project
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', project.id)
  event.target.style.opacity = '0.5'
}

// 拖拽结束
const handleDragEnd = (event) => {
  event.target.style.opacity = '1'
  draggedProject.value = null
  dragOverFolder.value = null
}

// 拖拽经过文件夹
const handleDragOver = (event, folder) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
  if (dragOverFolder.value?.id !== folder.id) {
    dragOverFolder.value = folder
  }
}

// 拖拽离开文件夹
const handleDragLeave = (event, folder) => {
  // 只有当真正离开文件夹元素时才清除高亮
  const rect = event.currentTarget.getBoundingClientRect()
  const x = event.clientX
  const y = event.clientY
  
  if (x < rect.left || x >= rect.right || y < rect.top || y >= rect.bottom) {
    if (dragOverFolder.value?.id === folder.id) {
      dragOverFolder.value = null
    }
  }
}

// 放置到文件夹
const handleDrop = async (event, folder) => {
  event.preventDefault()
  event.stopPropagation()
  dragOverFolder.value = null
  
  if (!draggedProject.value) {
    return
  }
  
  if (!folder || !folder.id) {
    draggedProject.value = null
    return
  }
  
  // 保存项目引用，防止在异步操作中被清空
  const project = draggedProject.value
  
  // 如果已经在这个文件夹中，不做任何操作
  if (project.folder_id === folder.id) {
    draggedProject.value = null
    return
  }
  
  try {
    // 直接更新项目的 folder_id
    await updateProject(project.id, {
      folder_id: folder.id
    })
    
    // 更新本地项目数据
    const index = projects.value.findIndex(p => p.id === project.id)
    if (index !== -1) {
      projects.value[index].folder_id = folder.id
    }
    
    toast.success(`已将项目移动到 ${folder.name}`)
    draggedProject.value = null
  } catch (err) {
    console.error('移动项目失败:', err)
    toast.error(err.response?.data?.error || '移动项目失败')
    draggedProject.value = null
  }
}

// 拖拽经过桌面
const handleDragOverDesktop = (event) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
  dragOverDesktop.value = true
}

// 拖拽离开桌面
const handleDragLeaveDesktop = (event) => {
  const rect = event.currentTarget.getBoundingClientRect()
  const x = event.clientX
  const y = event.clientY
  
  if (x < rect.left || x >= rect.right || y < rect.top || y >= rect.bottom) {
    dragOverDesktop.value = false
  }
}

// 放置到桌面
const handleDropToDesktop = async (event) => {
  event.preventDefault()
  event.stopPropagation()
  dragOverDesktop.value = false
  
  if (!draggedProject.value) {
    return
  }
  
  // 保存项目引用，防止在异步操作中被清空
  const project = draggedProject.value
  
  // 如果已经在桌面（没有 folder_id），不做任何操作
  if (!project.folder_id) {
    draggedProject.value = null
    return
  }
  
  try {
    // 将项目的 folder_id 设为 null
    await updateProject(project.id, {
      folder_id: null
    })
    
    // 更新本地项目数据
    const index = projects.value.findIndex(p => p.id === project.id)
    if (index !== -1) {
      projects.value[index].folder_id = null
    }
    
    toast.success('已将项目移到桌面')
    draggedProject.value = null
  } catch (err) {
    console.error('移动项目失败:', err)
    toast.error(err.response?.data?.error || '移动项目失败')
    draggedProject.value = null
  }
}

// 关闭项目弹窗
const closeModals = () => {
  showCreateModal.value = false
  showEditModal.value = false
  editTarget.value = null
  formData.value = { name: '', description: '', folder_id: selectedFolder.value?.id || null }
}

// 打开编辑文件夹弹窗
const openEditFolderModal = (folder) => {
  editFolderTarget.value = folder
  folderFormData.value = {
    name: folder.name,
    color: folder.color || 'blue'
  }
  showEditFolderModal.value = true
}

// 确认删除文件夹
const confirmDeleteFolder = (folder) => {
  deleteFolderTarget.value = folder
  showDeleteFolderModal.value = true
}

// 关闭文件夹弹窗
const closeFolderModals = () => {
  showCreateFolderModal.value = false
  showEditFolderModal.value = false
  editFolderTarget.value = null
  folderFormData.value = { name: '', color: 'blue' }
}

// 退出登录
const handleLogout = () => {
  authStore.logout()
  projects.value = []
  folders.value = []
  selectedFolder.value = null
  showUserProfileModal.value = false
  toast.success('已退出登录')
}

// 打开个人资料弹窗
const openUserProfileModal = () => {
  // 初始化表单数据为当前用户信息
  profileForm.value = {
    username: authStore.user?.username || '',
    email: authStore.user?.email || '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
  isEditingProfile.value = false
  showPasswordFields.value = false
  showUserProfileModal.value = true
}

// 开始编辑个人资料
const startEditingProfile = () => {
  // 确保表单数据是最新的
  profileForm.value = {
    username: authStore.user?.username || '',
    email: authStore.user?.email || '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
  isEditingProfile.value = true
  showPasswordFields.value = false
  passwordStep.value = 1
}

// 切换密码修改区域
const togglePasswordFields = () => {
  showPasswordFields.value = !showPasswordFields.value
  if (showPasswordFields.value) {
    passwordStep.value = 1
    profileForm.value.currentPassword = ''
    profileForm.value.newPassword = ''
    profileForm.value.confirmPassword = ''
  }
}

// 验证当前密码
const verifyCurrentPassword = async () => {
  if (!profileForm.value.currentPassword) {
    toast.warning('请输入当前密码')
    return
  }

  verifyingPassword.value = true
  try {
    // 调用后端API验证密码
    const response = await fetch('http://localhost:5000/api/auth/verify-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({
        password: profileForm.value.currentPassword
      })
    })

    const data = await response.json()

    if (response.ok && data.valid) {
      // 密码验证成功，进入下一步
      passwordStep.value = 2
      toast.success('密码验证成功，请设置新密码')
    } else {
      // 密码验证失败
      showError('当前密码不正确\n\n请确认：\n• 输入的密码是否正确\n• 密码区分大小写', '密码错误')
      profileForm.value.currentPassword = ''
    }
  } catch (err) {
    console.error('验证密码失败:', err)
    showError('验证密码时发生错误\n\n请检查网络连接后重试', '验证失败')
  } finally {
    verifyingPassword.value = false
  }
}

// 取消编辑个人资料
const cancelEditingProfile = () => {
  isEditingProfile.value = false
  showPasswordFields.value = false
  passwordStep.value = 1
  // 恢复为原始用户数据，而不是清空
  profileForm.value = {
    username: authStore.user?.username || '',
    email: authStore.user?.email || '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
}

// 关闭个人资料弹窗
const closeUserProfileModal = () => {
  showUserProfileModal.value = false
  cancelEditingProfile()
}

// 更新个人资料
// 更新个人资料
const handleUpdateProfile = async () => {
  // 验证表单
  if (!profileForm.value.username.trim()) {
    toast.warning('用户名不能为空')
    return
  }
  
  if (!profileForm.value.email.trim()) {
    toast.warning('邮箱不能为空')
    return
  }
  
  // 验证用户名长度
  if (profileForm.value.username.length < 2 || profileForm.value.username.length > 64) {
    toast.warning('用户名长度应为2-64个字符')
    return
  }
  
  // 验证邮箱格式
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(profileForm.value.email)) {
    toast.warning('请输入有效的邮箱地址')
    return
  }
  
  // 如果要修改密码，验证密码字段
  if (showPasswordFields.value) {
    // 如果还在步骤1，提示用户先验证当前密码
    if (passwordStep.value === 1) {
      toast.warning('请先验证当前密码')
      return
    }
    
    if (!profileForm.value.newPassword) {
      toast.warning('请输入新密码')
      return
    }
    
    if (profileForm.value.newPassword.length < 6) {
      toast.warning('新密码至少需要6个字符')
      return
    }
    
    if (profileForm.value.newPassword !== profileForm.value.confirmPassword) {
      toast.warning('两次输入的新密码不一致')
      return
    }
    
    if (profileForm.value.newPassword === profileForm.value.currentPassword) {
      toast.warning('新密码不能与当前密码相同')
      return
    }
  }
  
  submitting.value = true
  try {
    const updateData = {
      username: profileForm.value.username,
      email: profileForm.value.email
    }
    
    // 如果要修改密码，添加密码字段
    if (showPasswordFields.value && passwordStep.value === 2) {
      updateData.current_password = profileForm.value.currentPassword
      updateData.new_password = profileForm.value.newPassword
    }
    
    const result = await updateUserProfile(updateData)
    
    // 更新本地用户信息
    authStore.user = result.user
    localStorage.setItem('user', JSON.stringify(result.user))
    
    if (showPasswordFields.value) {
      toast.success('个人资料和密码更新成功')
    } else {
      toast.success('个人资料更新成功')
    }
    
    cancelEditingProfile()
  } catch (err) {
    console.error('更新个人资料失败:', err)
    
    // 根据不同的错误状态码显示不同的提示
    if (err.response) {
      const status = err.response.status
      const errorMsg = err.response.data?.error
      
      switch (status) {
        case 400:
          showError(errorMsg || '请求参数错误，请检查输入信息', '更新失败')
          break
        case 401:
          // 这里不应该再出现密码错误，因为已经在步骤1验证过了
          showError('认证失败，请重新登录', '认证错误')
          break
        case 409:
          // 冲突错误，用户名或邮箱已被使用
          if (errorMsg?.includes('用户名')) {
            showError('该用户名已被其他用户使用\n\n请更换一个新的用户名', '用户名冲突')
          } else if (errorMsg?.includes('邮箱')) {
            showError('该邮箱已被其他用户使用\n\n请更换一个新的邮箱', '邮箱冲突')
          } else {
            showError(errorMsg || '用户名或邮箱已被使用\n\n请更换后重试', '更新失败')
          }
          break
        case 500:
          showError('服务器错误，请稍后重试\n如果问题持续存在，请联系管理员', '服务器错误')
          break
        default:
          showError(errorMsg || '更新失败，请重试', '更新失败')
      }
    } else if (err.request) {
      showError('无法连接到服务器\n\n请检查：\n• 网络连接是否正常\n• 后端服务是否启动', '网络错误')
    } else {
      showError(err.message || '更新失败，请重试', '更新失败')
    }
  } finally {
    submitting.value = false
  }
}

// 更换头像
const handleChangeAvatar = () => {
  // 创建一个隐藏的文件选择器
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/jpeg,image/png,image/jpg,image/gif,image/webp'
  
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    
    // 验证文件大小（限制为5MB）
    const maxSize = 5 * 1024 * 1024
    if (file.size > maxSize) {
      toast.warning('图片大小不能超过5MB')
      return
    }
    
    // 验证文件类型
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif', 'image/webp']
    if (!validTypes.includes(file.type)) {
      toast.warning('只支持 JPG、PNG、GIF、WebP 格式的图片')
      return
    }
    
    // 上传头像
    await uploadAvatar(file)
  }
  
  input.click()
}

// 上传头像
const uploadAvatar = async (file) => {
  const formData = new FormData()
  formData.append('avatar', file)
  
  submitting.value = true
  try {
    const response = await fetch('http://localhost:5000/api/auth/avatar', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      },
      body: formData
    })
    
    const data = await response.json()
    
    if (response.ok) {
      // 更新本地用户信息
      authStore.user = data.user
      localStorage.setItem('user', JSON.stringify(data.user))
      toast.success('头像更新成功')
    } else {
      showError(data.error || '头像上传失败', '上传失败')
    }
  } catch (err) {
    console.error('上传头像失败:', err)
    showError('上传头像时发生错误\n\n请检查网络连接后重试', '上传失败')
  } finally {
    submitting.value = false
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  })
}

onMounted(() => {
  // 如果已登录，加载数据
  if (authStore.isAuthenticated) {
    fetchProjects()
    fetchFolders()
  }
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
