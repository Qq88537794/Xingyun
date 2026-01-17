-- =====================================================
-- 行云 (Xingyun) 数据库初始化脚本
-- 适用于 MySQL 8.0+
-- =====================================================

-- 创建数据库（如不存在）
CREATE DATABASE IF NOT EXISTS `xingyun` 
  DEFAULT CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

USE `xingyun`;

-- =====================================================
-- 1. 用户表 (users)
-- =====================================================
CREATE TABLE IF NOT EXISTS `users` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` VARCHAR(64) NOT NULL COMMENT '用户名',
  `email` VARCHAR(255) NOT NULL COMMENT '邮箱',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
  `avatar` VARCHAR(512) DEFAULT NULL COMMENT '头像URL',
  `description` TEXT DEFAULT NULL COMMENT '个人简介',
  `settings` JSON DEFAULT NULL COMMENT '用户设置',
  `last_login` TIMESTAMP NULL DEFAULT NULL COMMENT '最后登录时间',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- =====================================================
-- 2. 文件夹表 (folders)
-- =====================================================
CREATE TABLE IF NOT EXISTS `folders` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '文件夹ID',
  `user_id` BIGINT NOT NULL COMMENT '所属用户ID',
  `name` VARCHAR(128) NOT NULL COMMENT '文件夹名称',
  `color` VARCHAR(32) DEFAULT 'blue' COMMENT '文件夹颜色',
  `icon` VARCHAR(32) DEFAULT 'folder' COMMENT '图标类型',
  `parent_id` BIGINT DEFAULT NULL COMMENT '父文件夹ID（支持嵌套）',
  `sort_order` INT DEFAULT 0 COMMENT '排序顺序',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '是否已删除',
  `deleted_at` TIMESTAMP NULL DEFAULT NULL COMMENT '删除时间',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_parent_id` (`parent_id`),
  CONSTRAINT `fk_folders_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_folders_parent` FOREIGN KEY (`parent_id`) REFERENCES `folders` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件夹表';

-- =====================================================
-- 3. 项目表 (projects)
-- =====================================================
CREATE TABLE IF NOT EXISTS `projects` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '项目ID',
  `user_id` BIGINT NOT NULL COMMENT '所属用户ID',
  `folder_id` BIGINT DEFAULT NULL COMMENT '所属文件夹ID',
  `name` VARCHAR(128) NOT NULL COMMENT '项目名称',
  `description` TEXT DEFAULT NULL COMMENT '项目描述',
  `status` VARCHAR(32) DEFAULT 'active' COMMENT '项目状态: active, archived',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '是否已删除',
  `deleted_at` TIMESTAMP NULL DEFAULT NULL COMMENT '删除时间',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_folder_id` (`folder_id`),
  CONSTRAINT `fk_projects_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_projects_folder` FOREIGN KEY (`folder_id`) REFERENCES `folders` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目表';

-- =====================================================
-- 4. 项目资源表 (project_resources)
-- =====================================================
CREATE TABLE IF NOT EXISTS `project_resources` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '资源ID',
  `project_id` BIGINT NOT NULL COMMENT '所属项目ID',
  `filename` VARCHAR(255) NOT NULL COMMENT '原始文件名',
  `file_path` VARCHAR(512) NOT NULL COMMENT '文件存储路径',
  `storage_provider` VARCHAR(32) DEFAULT 'local' COMMENT '存储提供商: local, oss, s3',
  `mime_type` VARCHAR(128) DEFAULT NULL COMMENT 'MIME类型',
  `file_size` BIGINT DEFAULT 0 COMMENT '文件大小（字节）',
  `parsing_status` VARCHAR(32) DEFAULT 'pending' COMMENT '解析状态: pending, processing, completed, failed',
  `vector_collection_id` VARCHAR(128) DEFAULT NULL COMMENT '向量数据库集合ID',
  `error_msg` TEXT DEFAULT NULL COMMENT '错误信息',
  `uploaded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '是否已删除',
  `deleted_at` TIMESTAMP NULL DEFAULT NULL COMMENT '删除时间',
  PRIMARY KEY (`id`),
  KEY `idx_project_id` (`project_id`),
  KEY `idx_parsing_status` (`parsing_status`),
  CONSTRAINT `fk_resources_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目资源表';

-- =====================================================
-- 初始化完成
-- =====================================================
