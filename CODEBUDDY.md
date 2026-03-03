# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

## Project Overview

湖南省二附院精致饮片复核系统 (Hunan Second Hospital Refined Herbal Pieces Review System) - A hospital-level Chinese herbal pieces review management system that implements QR code-based scanning review, intelligent error alerts, basket-based review, full-process traceability, and workload statistics.

## Quick Start

```bash
# Check if ports 8000/3000 are occupied (with option to kill)
sh check_port.sh

# Start both backend and frontend (handles venv, npm install, and servers)
sh start_system.sh

# Stop all services
sh stop_system.sh

# Access points:
# - Frontend: http://localhost:3000 (auto-switches to 3001 if port busy)
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/zyfh/api/v1/docs
```

### Manual Start

```bash
# Backend
python3 -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements.txt  # Windows
.venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

## Architecture

### Backend Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI application with all API endpoints (~2000 lines)
│   ├── models.py        # SQLAlchemy ORM models (25+ tables)
│   ├── schemas.py       # Pydantic request/response schemas
│   └── database.py      # Database connection configuration
├── tests/               # pytest test files
├── requirements.txt     # Python dependencies
└── openapi.yaml         # OpenAPI specification
```

### Frontend Structure

```
frontend/
├── src/
│   ├── views/           # Vue components (Dashboard, Login, QRCode, Check, Basket, Alert, Trace, Statistics, System)
│   ├── api/             # API service layer
│   ├── stores/          # Pinia state management
│   ├── router/          # Vue Router configuration
│   └── utils/           # Utility functions
├── sw.js                # Service Worker for PWA offline support
└── vite.config.js       # Vite build configuration
```

### Core Modules

1. **QR Code Management** (`/zyfh/api/v1/qrcode/*`)
   - Single/batch QR code generation with data validation
   - QR code parsing and verification
   - Enterprise and drug info management

2. **Scanning Review** (`/zyfh/api/v1/check/*`)
   - HIS prescription synchronization
   - Real-time scanning with offline support
   - Progress saving and resume capability

3. **Error Alerts** (`/zyfh/api/v1/alert/*`)
   - Drug/quantity error detection
   - Error handling workflow

4. **Basket Management** (`/zyfh/api/v1/basket/*`)
   - Prescription-to-basket-to-drug association
   - Basket review confirmation

5. **Traceability** (`/zyfh/api/v1/trace/*`)
   - Operation log queries
   - Video monitoring integration
   - Traceability report generation

6. **Workload Statistics** (`/zyfh/api/v1/stat/*`)
   - Multi-dimensional statistics (user, time, prescription)
   - Report generation

7. **System Management** (`/zyfh/api/v1/sys/*`)
   - User/role/device management
   - Drug data sync from HIS
   - System logs and data backup

### Key Technical Details

- **QR Code Format**: `{enterprise_code};{cj_id};{spec};{batch_no};{num};{weight}` encoded as GB2312 then Base64
- **Offline Support**: Local SQLite (`local_offline.db`) caches scan records, progress, and submissions; auto-syncs on network recovery
- **Authentication**: JWT tokens with 24-hour expiry; MD5 password hashing
- **API Response Format**: `{code, msg, data, timestamp, requestId}`
- **Business Codes**: `0000`=success, `1000`=parameter error, `2000`=auth error, `7000`=QR error, `8000`=business error

### Database Tables

- **base_enterprise**: Enterprise master data
- **base_drug_info**: Drug master data (synced from HIS)
- **qrcode_generate_record/verify_record**: QR code lifecycle
- **his_prescription_sync**: HIS prescription sync cache
- **drug_check_main/detail/progress**: Review workflow
- **basket_manage/pres_basket_relation**: Basket management
- **check_error_record/handle**: Error tracking
- **check_operate_record**: Operation audit log
- **video_monitor_link**: Video integration
- **check_workload_stat**: Statistics aggregation
- **sys_user/role/user_role/device_manage**: System management

### Default Credentials

- Admin account: `admin` / `admin123`
- Pre-configured enterprises: 6 pharmaceutical companies
- Pre-configured roles: SUPER_ADMIN, SYS_ADMIN, QR_MANAGER, REVIEWER, VIEWER, TRACE_MANAGER
