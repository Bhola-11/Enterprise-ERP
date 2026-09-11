# Enterprise-ERP (Nexora Enterprise OS)

[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)]()
[![Status](https://img.shields.io/badge/Release-v1.0.0--Production-success.svg)]()

**Nexora Enterprise OS** is a unified, mission-critical Enterprise Resource Planning (ERP) and Business Operating System designed for medium and large-scale enterprises. It seamlessly orchestrates 24 integrated business domains into a single, cohesive, high-performance platform.

---

## 🌟 Architecture & Key Modules

1. **Executive Dashboard**: Real-time business intelligence, dynamic KPI metrics, cashflow, P&L widgets, and multi-period filters.
2. **CRM & Pipeline**: Leads, Contacts, Accounts, Visual Opportunity Stages, Deals, Activities & Conversion.
3. **Sales & Revenue**: Quotations, Sales Orders, Invoices, Delivery Notes, Credit Notes & Payment tracking.
4. **Purchasing & Supplier Management**: RFQ, Vendor Quotations, Purchase Orders, Goods Receipt (GRN), Vendor Bills.
5. **Procurement**: Vendor scorecards, spending threshold policies, multi-level purchase rules.
6. **Inventory & Stock Movements**: Multi-variant SKU/Barcode catalog, Batch/Serial tracking, immutable Stock Movement Ledger.
7. **Warehouse Management**: Multi-warehouse hierarchy (Zones, Aisles, Shelves, Bins), Pick/Pack/Ship, Transfers, Stock Auditing.
8. **Double-Entry Accounting**: Full General Ledger, Chart of Accounts, Journal Entries, AR/AP Aging, P&L, Balance Sheet, Cash Flow.
9. **Human Resources (HR)**: Employee Directory, Org Chart, Attendance, Shift Management, Leaves & Document Vault.
10. **Payroll Engine**: Dynamic Salary Components, Payrun cycles, Tax bracket deductions, Payslip generation.
11. **Project Management**: Project portfolios, Milestones, Interactive Kanban, Task dependencies, Timesheets & Budgets.
12. **Customer Support**: Helpdesk ticketing system, SLAs, priority escalation, internal notes, audit history.
13. **Fixed Asset Management**: Asset tracking, warranty, maintenance logs, straight-line & declining depreciation schedules.
14. **Fleet & Logistics**: Fleet registry, Driver management, Fuel logs, Service schedules, GPS trip logs.
15. **Manufacturing & MRP**: Multi-level Bill of Materials (BOM), Work Centers, Production Orders, Material Issuance & QC inspections.
16. **Document Management System (DMS)**: Hierarchical folders, access control, version histories & audit tracking.
17. **Workflow & Approval Engine**: Configurable multi-tier approval rules across Purchase, Expenses, Leaves, Orders and Discounts.
18. **Centralized Notifications**: In-app notifications, user preferences, email/webhook notification dispatchers.
19. **Reporting & Analytics**: Comprehensive analytical reporting with dynamic filters, CSV and JSON data export.
20. **Audit & Compliance**: Automated mutation logging, IP tracking, old/new state diffs, compliance ledger.
21. **User & Role Management (RBAC)**: Granular role-based access control with module & object-level permissions.
22. **Organization Management**: Multi-branch support, Departments, Cost Centers, Fiscal Years, Tax regimes.
23. **System Settings**: Enterprise-wide configuration, currencies, locales, email settings & backup preferences.
24. **REST API & Integrations**: Full REST API endpoints, token authentication, swagger documentation schemas.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- SQLite (or PostgreSQL/MySQL for production scale)

### 2. Setup Virtual Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Migrations & Seed Sample Data
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_enterprise_data
```

### 5. Launch Development Server
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/` to explore the Landing Page or login directly at `http://127.0.0.1:8000/login/`.

**Default Superadmin Credentials:**
- Email: `admin@nexora.com`
- Password: `AdminPassword123!`

---

## 🔒 Security & Architecture Standards
- Standard Django ORM with full relational indexing and transactional guarantees.
- Zero raw unescaped SQL injections; comprehensive CSRF and XSS protection.
- Immutable stock and financial ledgers with double-entry balance verification.
- Reusable modular apps designed for clean maintainability and horizontal scalability.
