-- 创建文件夹表
CREATE TABLE IF NOT EXISTS `folders` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `name` VARCHAR(128) NOT NULL,
  `color` VARCHAR(32) DEFAULT 'blue',
  `icon` VARCHAR(32) DEFAULT 'folder',
  `parent_id` BIGINT DEFAULT NULL,
  `sort_order` INT DEFAULT 0,
  `is_deleted` TINYINT(1) DEFAULT 0,
  `deleted_at` TIMESTAMP NULL DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_parent_id` (`parent_id`),
  CONSTRAINT `fk_folders_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_folders_parent` FOREIGN KEY (`parent_id`) REFERENCES `folders` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 给 projects 表添加 folder_id 字段
ALTER TABLE `projects` ADD COLUMN `folder_id` BIGINT DEFAULT NULL AFTER `user_id`;
ALTER TABLE `projects` ADD KEY `idx_folder_id` (`folder_id`);
ALTER TABLE `projects` ADD CONSTRAINT `fk_projects_folder` FOREIGN KEY (`folder_id`) REFERENCES `folders` (`id`) ON DELETE SET NULL;
