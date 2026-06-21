USE scc_osp2026;

ALTER TABLE complaints
    ADD COLUMN ai_urgency VARCHAR(20) NOT NULL DEFAULT '보통' AFTER ai_confidence,
    ADD COLUMN final_urgency VARCHAR(20) NOT NULL DEFAULT '보통' AFTER ai_urgency,
    ADD COLUMN urgency_confidence FLOAT NULL AFTER final_urgency;

ALTER TABLE complaint_status_history
    ADD COLUMN prev_final_urgency VARCHAR(20) AFTER new_final_category,
    ADD COLUMN new_final_urgency VARCHAR(20) AFTER prev_final_urgency;

CREATE INDEX idx_complaints_final_urgency ON complaints(final_urgency);
