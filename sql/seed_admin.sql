USE scc_osp2026;

INSERT INTO admins (username, password_hash, display_name, role)
VALUES ('admin', SHA2('admin1234', 256), '데모 관리자', 'admin')
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    display_name = VALUES(display_name),
    role = VALUES(role);
