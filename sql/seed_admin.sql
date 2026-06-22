USE scc_osp2026;

INSERT INTO admins (username, password_hash, display_name, role, region_name, school_name)
VALUES ('admin', SHA2('admin1234', 256), '데모 관리자', 'admin', '서울시교육청', '새봄초등학교')
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    display_name = VALUES(display_name),
    role = VALUES(role),
    region_name = VALUES(region_name),
    school_name = VALUES(school_name);
