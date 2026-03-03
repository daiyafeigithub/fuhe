-- PoC minimal schema for prescriptions, devices and audit
CREATE TABLE IF NOT EXISTS prescriptions (
  id VARCHAR(64) PRIMARY KEY,
  patient_name VARCHAR(128),
  status VARCHAR(32),
  payload JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS devices (
  device_id VARCHAR(64) PRIMARY KEY,
  info JSON,
  status VARCHAR(32),
  last_heartbeat TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  user VARCHAR(64),
  action VARCHAR(128),
  detail JSON
);
