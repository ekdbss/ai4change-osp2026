USE scc_osp2026;

ALTER TABLE users
    ADD COLUMN school_name VARCHAR(100) AFTER phone_masked,
    ADD COLUMN student_grade VARCHAR(20) AFTER school_name,
    ADD COLUMN student_class VARCHAR(50) AFTER student_grade,
    ADD COLUMN student_number VARCHAR(20) AFTER student_class,
    ADD COLUMN student_name VARCHAR(100) AFTER student_number;

ALTER TABLE admins
    ADD COLUMN region_name VARCHAR(100) AFTER role,
    ADD COLUMN school_name VARCHAR(100) AFTER region_name;

CREATE INDEX idx_users_student
    ON users(school_name, student_grade, student_class, student_number, student_name);
