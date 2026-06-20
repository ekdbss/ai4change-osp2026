USE scc_osp2026;

INSERT INTO admins (username, password_hash, role)
VALUES ('admin', 'change-this-password-hash', 'admin')
ON DUPLICATE KEY UPDATE username = username;
