CREATE DATABASE IF NOT EXISTS scc_osp2026
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE scc_osp2026;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    parent_type VARCHAR(50),
    phone_masked VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admins (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'teacher',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS complaints (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NULL,
    title VARCHAR(255) NOT NULL,
    original_text TEXT NOT NULL,
    masked_text TEXT,
    refined_text TEXT NOT NULL,
    structured_json JSON NOT NULL,
    category VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT '접수',
    recommended_department VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_complaints_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS complaint_status_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    complaint_id BIGINT NOT NULL,
    admin_id BIGINT NULL,
    prev_status VARCHAR(30),
    new_status VARCHAR(30) NOT NULL,
    memo TEXT,
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

CREATE INDEX idx_complaints_category ON complaints(category);
CREATE INDEX idx_complaints_status ON complaints(status);
CREATE INDEX idx_complaints_created_at ON complaints(created_at);
