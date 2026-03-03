-- 精致饮片复核系统 MySQL 数据库初始化脚本
-- 数据库创建
CREATE DATABASE IF NOT EXISTS zyyz_fuping DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE zyyz_fuping;

-- ===== 基础配置表 =====

-- 1. 企业标志表
CREATE TABLE IF NOT EXISTS base_enterprise (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  enterprise_code INT NOT NULL UNIQUE,
  enterprise_name VARCHAR(100) NOT NULL,
  status TINYINT NOT NULL DEFAULT 1,
  create_by VARCHAR(20) NOT NULL,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_by VARCHAR(20),
  update_time DATETIME,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_enterprise_name (enterprise_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 2. 院内药品基础表
CREATE TABLE IF NOT EXISTS base_drug_info (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  cj_id VARCHAR(20) NOT NULL UNIQUE,
  drug_name VARCHAR(50) NOT NULL,
  drug_type VARCHAR(30),
  spec_range VARCHAR(50),
  his_sync_time DATETIME NOT NULL,
  status TINYINT NOT NULL DEFAULT 1,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME,
  is_delete TINYINT NOT NULL DEFAULT 0,
  ext1 VARCHAR(50),
  ext2 VARCHAR(50),
  KEY idx_drug_name (drug_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ===== 二维码管理表 =====

-- 3. 二维码生成记录表
CREATE TABLE IF NOT EXISTS qrcode_generate_record (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  qrcode_id VARCHAR(30) NOT NULL UNIQUE,
  enterprise_code INT NOT NULL,
  cj_id VARCHAR(20) NOT NULL,
  spec VARCHAR(10) NOT NULL,
  batch_no VARCHAR(10) NOT NULL,
  num INT NOT NULL DEFAULT 7,
  weight DECIMAL(8,4) NOT NULL,
  qrcode_origin VARCHAR(200) NOT NULL,
  base64_str TEXT NOT NULL,
  qrcode_url VARCHAR(255) NOT NULL,
  generate_by VARCHAR(20) NOT NULL,
  generate_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_enterprise_code (enterprise_code),
  KEY idx_cj_batch (cj_id, batch_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 4. 二维码校验记录表
CREATE TABLE IF NOT EXISTS qrcode_verify_record (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  qrcode_id VARCHAR(30) NOT NULL,
  verify_base64 TEXT NOT NULL,
  decrypt_origin VARCHAR(200) NOT NULL,
  verify_result VARCHAR(10) NOT NULL,
  verify_reason VARCHAR(200),
  verify_by VARCHAR(20) NOT NULL,
  verify_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_qrcode_id (qrcode_id),
  KEY idx_verify_result (verify_result),
  KEY idx_verify_time (verify_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ===== 扫码复核表 =====

-- 5. HIS处方同步表
CREATE TABLE IF NOT EXISTS his_prescription_sync (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  pres_no VARCHAR(30) NOT NULL UNIQUE,
  patient_name VARCHAR(20) NOT NULL,
  patient_id VARCHAR(30),
  dept_name VARCHAR(30) NOT NULL,
  doc_name VARCHAR(20) NOT NULL,
  pres_time DATETIME NOT NULL,
  drug_total INT NOT NULL,
  sync_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  pres_status TINYINT NOT NULL DEFAULT 1,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_pres_time (pres_time),
  KEY idx_pres_status (pres_status),
  KEY idx_dept_name (dept_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 6. 饮片复核主表
CREATE TABLE IF NOT EXISTS drug_check_main (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  pres_no VARCHAR(30) NOT NULL UNIQUE,
  check_by VARCHAR(20) NOT NULL,
  check_station VARCHAR(10) NOT NULL,
  check_start_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  check_end_time DATETIME,
  check_status TINYINT NOT NULL DEFAULT 1,
  check_qualified TINYINT,
  error_total INT NOT NULL DEFAULT 0,
  submit_by VARCHAR(20),
  submit_time DATETIME,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_check_by (check_by),
  KEY idx_check_status (check_status),
  KEY idx_check_start_time (check_start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 7. 饮片复核明细表
CREATE TABLE IF NOT EXISTS drug_check_detail (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  check_main_id BIGINT NOT NULL,
  pres_no VARCHAR(30) NOT NULL,
  cj_id VARCHAR(20) NOT NULL,
  drug_name VARCHAR(50) NOT NULL,
  spec VARCHAR(10) NOT NULL,
  pres_num INT NOT NULL,
  qrcode_id VARCHAR(30) NOT NULL,
  scan_spec VARCHAR(10) NOT NULL,
  scan_num INT NOT NULL,
  scan_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  basket_no VARCHAR(20) NOT NULL,
  scan_result TINYINT NOT NULL DEFAULT 0,
  is_check TINYINT NOT NULL DEFAULT 0,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_main_cj (check_main_id, cj_id),
  KEY idx_pres_no (pres_no),
  KEY idx_qrcode_id (qrcode_id),
  KEY idx_basket_no (basket_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 8. 复核进度表
CREATE TABLE IF NOT EXISTS drug_check_progress (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  check_main_id BIGINT NOT NULL UNIQUE,
  pres_no VARCHAR(30) NOT NULL,
  finished_drug INT NOT NULL DEFAULT 0,
  unfinish_drug INT NOT NULL DEFAULT 0,
  current_basket VARCHAR(20) NOT NULL,
  progress_json TEXT NOT NULL,
  save_by VARCHAR(20) NOT NULL,
  save_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_pres_no (pres_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ===== 分筐复核表 =====

-- 9. 筐号管理表
CREATE TABLE IF NOT EXISTS basket_manage (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  basket_no VARCHAR(20) NOT NULL UNIQUE,
  basket_name VARCHAR(50),
  create_type TINYINT NOT NULL DEFAULT 1,
  status TINYINT NOT NULL DEFAULT 1,
  create_by VARCHAR(20) NOT NULL,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 10. 处方分筐关联表
CREATE TABLE IF NOT EXISTS pres_basket_relation (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  pres_no VARCHAR(30) NOT NULL,
  check_main_id BIGINT NOT NULL,
  basket_no VARCHAR(20) NOT NULL,
  cj_id VARCHAR(20) NOT NULL,
  drug_name VARCHAR(50),
  basket_drug_num INT NOT NULL,
  basket_status TINYINT NOT NULL DEFAULT 1,
  create_by VARCHAR(20) NOT NULL,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_pres_basket (pres_no, basket_no),
  KEY idx_basket_cj (basket_no, cj_id),
  KEY idx_basket_status (basket_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ===== 错误提醒表 =====

-- 11. 复核错误记录表
CREATE TABLE IF NOT EXISTS check_error_record (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  check_detail_id BIGINT NOT NULL UNIQUE,
  check_main_id BIGINT NOT NULL,
  pres_no VARCHAR(30) NOT NULL,
  cj_id VARCHAR(20) NOT NULL,
  error_type VARCHAR(20) NOT NULL,
  error_desc VARCHAR(200) NOT NULL,
  pres_standard VARCHAR(50) NOT NULL,
  scan_actual VARCHAR(50) NOT NULL,
  error_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  error_status TINYINT NOT NULL DEFAULT 1,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_pres_no (pres_no),
  KEY idx_error_type (error_type),
  KEY idx_error_status (error_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 12. 错误处理记录表
CREATE TABLE IF NOT EXISTS check_error_handle (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  error_id BIGINT NOT NULL UNIQUE,
  check_detail_id BIGINT NOT NULL,
  pres_no VARCHAR(30) NOT NULL,
  handle_type VARCHAR(20) NOT NULL,
  handle_desc VARCHAR(200) NOT NULL,
  handle_by VARCHAR(20) NOT NULL,
  handle_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_pres_no (pres_no),
  KEY idx_handle_by (handle_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ===== 溯源管理表 =====

-- 13. 复核操作记录表
CREATE TABLE IF NOT EXISTS check_operate_record (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  pres_no VARCHAR(30),
  check_main_id BIGINT,
  operate_user VARCHAR(20) NOT NULL,
  operate_module VARCHAR(20) NOT NULL,
  operate_type VARCHAR(20) NOT NULL,
  operate_desc VARCHAR(200) NOT NULL,
  operate_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  operate_ip VARCHAR(20),
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_pres_no (pres_no),
  KEY idx_operate_user (operate_user),
  KEY idx_operate_module (operate_module),
  KEY idx_operate_time (operate_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 14. 视频监控联动表
CREATE TABLE IF NOT EXISTS video_monitor_link (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  check_detail_id BIGINT NOT NULL UNIQUE,
  pres_no VARCHAR(30) NOT NULL,
  scan_time DATETIME NOT NULL,
  check_station VARCHAR(10) NOT NULL,
  camera_no VARCHAR(20) NOT NULL,
  video_url VARCHAR(255) NOT NULL,
  video_download VARCHAR(255) NOT NULL,
  video_snapshot VARCHAR(255) NOT NULL,
  video_valid_time DATETIME NOT NULL,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_pres_no (pres_no),
  KEY idx_scan_time (scan_time),
  KEY idx_check_station (check_station)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ===== 工作量统计表 =====

-- 15. 复核工作量统计主表
CREATE TABLE IF NOT EXISTS check_workload_stat (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  check_by VARCHAR(20) NOT NULL,
  stat_time_type VARCHAR(10) NOT NULL,
  stat_time VARCHAR(20) NOT NULL,
  pres_total INT NOT NULL DEFAULT 0,
  drug_total INT NOT NULL DEFAULT 0,
  qrcode_total INT NOT NULL DEFAULT 0,
  qualified_pres INT NOT NULL DEFAULT 0,
  error_total INT NOT NULL DEFAULT 0,
  handle_error INT NOT NULL DEFAULT 0,
  check_hours DECIMAL(5,2),
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_user_stat (check_by, stat_time_type, stat_time),
  KEY idx_stat_time (stat_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ===== 系统基础表 =====

-- 16. 系统用户表
CREATE TABLE IF NOT EXISTS sys_user (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_account VARCHAR(20) NOT NULL UNIQUE,
  user_pwd VARCHAR(64) NOT NULL,
  user_name VARCHAR(20) NOT NULL,
  dept_name VARCHAR(30) NOT NULL,
  post VARCHAR(20) NOT NULL,
  phone VARCHAR(11),
  status TINYINT NOT NULL DEFAULT 1,
  login_time DATETIME,
  login_ip VARCHAR(20),
  create_by VARCHAR(20) NOT NULL,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_by VARCHAR(20),
  update_time DATETIME,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_user_name (user_name),
  KEY idx_dept_name (dept_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 17. 角色权限表
CREATE TABLE IF NOT EXISTS sys_role (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  role_code VARCHAR(20) NOT NULL UNIQUE,
  role_name VARCHAR(20) NOT NULL,
  role_permission TEXT NOT NULL,
  role_desc VARCHAR(100),
  status TINYINT NOT NULL DEFAULT 1,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_role_name (role_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 18. 用户角色关联表
CREATE TABLE IF NOT EXISTS sys_user_role (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  role_id BIGINT NOT NULL,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_user_role (user_id, role_id),
  KEY idx_user_id (user_id),
  KEY idx_role_id (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ===== 设备管理表 =====

-- 19. 硬件设备管理表
CREATE TABLE IF NOT EXISTS sys_device_manage (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  device_no VARCHAR(30) NOT NULL UNIQUE,
  device_type VARCHAR(20) NOT NULL,
  device_name VARCHAR(50) NOT NULL,
  bind_station VARCHAR(10),
  bind_user VARCHAR(20),
  device_status VARCHAR(10) NOT NULL DEFAULT 'ONLINE',
  last_use_time DATETIME,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME,
  is_delete TINYINT NOT NULL DEFAULT 0,
  KEY idx_device_type (device_type),
  KEY idx_device_status (device_status),
  KEY idx_bind_station (bind_station)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ===== 初始化数据 =====

-- 初始化企业标志表（5家企业）
INSERT INTO base_enterprise (enterprise_code, enterprise_name, status, create_by, create_time, is_delete)
VALUES 
(1, '亳州市沪谯药业有限公司', 1, 'admin', NOW(), 0),
(2, '湖南三湘中药饮片有限公司', 1, 'admin', NOW(), 0),
(3, '长沙新林制药有限公司', 1, 'admin', NOW(), 0),
(4, '安徽亳药千草中药饮片有限公司', 1, 'admin', NOW(), 0),
(5, '北京仟草中药饮片有限公司', 1, 'admin', NOW(), 0),
(6, '天津尚药堂制药有限公司', 1, 'admin', NOW(), 0)
ON DUPLICATE KEY UPDATE enterprise_name=VALUES(enterprise_name);

-- 初始化系统角色表
INSERT INTO sys_role (role_code, role_name, role_permission, role_desc, status, create_time, is_delete)
VALUES 
('ADMIN', '超级管理员', 'all', '系统最高权限，拥有所有功能操作权限', 1, NOW(), 0),
('SYS_MANAGE', '系统管理员', 'sys:user,sys:role,sys:device,base:enterprise,base:drug', '系统基础配置、用户权限、设备管理', 1, NOW(), 0),
('QRCODE_MANAGE', '二维码管理员', 'qrcode:generate,qrcode:verify,qrcode:query', '二维码生成、校验、查询管理', 1, NOW(), 0),
('CHECKER', '复核员', 'check:scan,check:save,check:submit,basket:manage,basket:relation,error:handle', '饮片扫码复核、分筐、错误处理', 1, NOW(), 0),
('QUERY', '查询员', 'check:query,trace:query,stat:query', '复核记录、溯源、工作量查询', 1, NOW(), 0),
('TRACE_ADMIN', '溯源管理员', 'trace:query,trace:video,trace:report', '溯源记录、视频查看、溯源报告生成', 1, NOW(), 0)
ON DUPLICATE KEY UPDATE role_name=VALUES(role_name);

-- 初始化默认管理员用户（密码: admin123，MD5值）
INSERT INTO sys_user (user_account, user_pwd, user_name, dept_name, post, status, create_by, create_time, is_delete)
VALUES 
('admin', '0192023a7bbd73250516f069df18b500', '超级管理员', '系统管理', '管理员', 1, 'init', NOW(), 0)
ON DUPLICATE KEY UPDATE user_name=VALUES(user_name);

-- 初始化管理员角色绑定
INSERT INTO sys_user_role (user_id, role_id, create_time, is_delete)
SELECT u.id, r.id, NOW(), 0 FROM sys_user u, sys_role r
WHERE u.user_account = 'admin' AND r.role_code = 'ADMIN'
ON DUPLICATE KEY UPDATE create_time=VALUES(create_time);
