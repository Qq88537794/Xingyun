-- 为 AI 聊天历史记录表添加 document_id 字段
ALTER TABLE ai_chat_history 
ADD COLUMN document_id VARCHAR(255) AFTER project_id;

-- 创建索引以提高查询性能
CREATE INDEX idx_ai_chat_history_document_id ON ai_chat_history(document_id);

-- 更新视图
DROP VIEW IF EXISTS ai_chat_history_recent;
CREATE VIEW ai_chat_history_recent AS
SELECT * FROM ai_chat_history
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 3 DAY)
ORDER BY created_at DESC;
