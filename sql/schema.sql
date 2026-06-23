CREATE DATABASE IF NOT EXISTS scc_osp2026
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE scc_osp2026;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    login_id VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    parent_name VARCHAR(100),
    parent_type VARCHAR(50),
    phone_masked VARCHAR(50),
    school_name VARCHAR(100),
    student_grade VARCHAR(20),
    student_class VARCHAR(50),
    student_number VARCHAR(20),
    student_name VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admins (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    role VARCHAR(50) NOT NULL DEFAULT 'teacher',
    region_name VARCHAR(100),
    school_name VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS category_priority_settings (
    category VARCHAR(50) PRIMARY KEY,
    priority_level TINYINT NOT NULL DEFAULT 3,
    description VARCHAR(255),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_category_priority_level
        CHECK (priority_level BETWEEN 1 AND 5)
);

CREATE TABLE IF NOT EXISTS complaints (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NULL,

    school_name VARCHAR(100) NOT NULL,
    student_grade VARCHAR(20),
    student_class VARCHAR(50) NOT NULL,
    student_number VARCHAR(20),
    student_name VARCHAR(100) NOT NULL,

    title VARCHAR(255) NOT NULL,
    original_text TEXT NOT NULL,
    masked_text TEXT,
    refined_text TEXT NOT NULL,
    structured_json JSON NULL,

    ai_category VARCHAR(50) NOT NULL,
    final_category VARCHAR(50),
    ai_confidence FLOAT NULL,
    ai_urgency VARCHAR(20) NOT NULL DEFAULT '보통',
    final_urgency VARCHAR(20) NOT NULL DEFAULT '보통',
    urgency_confidence FLOAT NULL,
    priority_level TINYINT NOT NULL DEFAULT 3,

    status VARCHAR(30) NOT NULL DEFAULT '접수',
    recommended_department VARCHAR(100),
    parent_visible_comment TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_complaints_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE SET NULL,
    CONSTRAINT chk_complaint_priority_level
        CHECK (priority_level BETWEEN 1 AND 5)
);

CREATE TABLE IF NOT EXISTS complaint_attachments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    complaint_id BIGINT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100),
    file_size BIGINT,
    file_path VARCHAR(500),
    file_data LONGBLOB NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_attachment_complaint
        FOREIGN KEY (complaint_id) REFERENCES complaints(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS complaint_status_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    complaint_id BIGINT NOT NULL,
    admin_id BIGINT NULL,

    prev_status VARCHAR(30),
    new_status VARCHAR(30) NOT NULL,
    prev_final_category VARCHAR(50),
    new_final_category VARCHAR(50),
    prev_final_urgency VARCHAR(20),
    new_final_urgency VARCHAR(20),
    prev_priority_level TINYINT,
    new_priority_level TINYINT,

    memo TEXT,
    is_parent_visible BOOLEAN NOT NULL DEFAULT TRUE,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_history_complaint
        FOREIGN KEY (complaint_id) REFERENCES complaints(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_history_admin
        FOREIGN KEY (admin_id) REFERENCES admins(id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS statistics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stat_date DATE NOT NULL,
    category VARCHAR(50) NOT NULL,
    total_count INT NOT NULL DEFAULT 0,
    pending_count INT NOT NULL DEFAULT 0,
    completed_count INT NOT NULL DEFAULT 0,
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_stat_category_date (stat_date, category)
);

INSERT INTO category_priority_settings (category, priority_level, description)
VALUES
    ('수업/학습 문제', 2, '수업 운영, 학습 지원, 평가 관련 민원'),
    ('교사 태도/행동', 1, '교사 언행, 상담, 관계 관련 민원'),
    ('시설/환경', 3, '교실, 냉난방, 화장실, 통학 환경 관련 민원'),
    ('급식', 3, '급식 품질, 위생, 알레르기 관련 민원'),
    ('생활지도/안전', 1, '학생 안전, 학교폭력, 생활지도 관련 민원'),
    ('기타', 4, '분류가 명확하지 않은 일반 문의')
ON DUPLICATE KEY UPDATE
    priority_level = VALUES(priority_level),
    description = VALUES(description);

CREATE INDEX idx_users_login_id ON users(login_id);
CREATE INDEX idx_users_student ON users(school_name, student_grade, student_class, student_number, student_name);

CREATE INDEX idx_complaints_user_id ON complaints(user_id);
CREATE INDEX idx_complaints_ai_category ON complaints(ai_category);
CREATE INDEX idx_complaints_final_category ON complaints(final_category);
CREATE INDEX idx_complaints_final_urgency ON complaints(final_urgency);
CREATE INDEX idx_complaints_status ON complaints(status);
CREATE INDEX idx_complaints_priority ON complaints(priority_level);
CREATE INDEX idx_complaints_created_at ON complaints(created_at);
CREATE INDEX idx_complaints_school ON complaints(school_name);

CREATE INDEX idx_attachments_complaint_id ON complaint_attachments(complaint_id);

CREATE INDEX idx_history_complaint_id ON complaint_status_history(complaint_id);
CREATE INDEX idx_history_changed_at ON complaint_status_history(changed_at);
