-- AI 聊天历史记录表
CREATE TABLE IF NOT EXISTS ai_chat_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    project_id BIGINT,
    session_id VARCHAR(255),
    request_type VARCHAR(50) NOT NULL,  -- 'chat', 'outline', 'expand', 'locate' 等
    user_message TEXT,
    ai_response TEXT NOT NULL,
    tokens_used INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);

-- 创建索引以提高查询性能
CREATE INDEX idx_ai_chat_history_user_id ON ai_chat_history(user_id);
CREATE INDEX idx_ai_chat_history_created_at ON ai_chat_history(created_at);
CREATE INDEX idx_ai_chat_history_session_id ON ai_chat_history(session_id);

-- 创建视图，方便查询最近3天的记录
CREATE OR REPLACE VIEW ai_chat_history_recent AS
SELECT * FROM ai_chat_history
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 3 DAY)
ORDER BY created_at DESC;
