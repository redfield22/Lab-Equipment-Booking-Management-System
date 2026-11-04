# Lab Inventory Management System

![Django](https://img.shields.io/badge/Django-5.x-092E20?logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?logo=bootstrap&logoColor=white)
![Database](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-See%20LICENSE-blue)

A comprehensive, database-backed laboratory inventory and booking management web application built with Django, Bootstrap 5, ReportLab, openpyxl, and qrcode.

Designed for academic institutions and laboratory administrators to register departments, track physical resources, handle student loan requests, verify equipment returns, log damages, alert administrators about stock shortages, and generate downloadable analytics reports.

---

## Table of Contents

- [Technical Stack & Libraries](#technical-stack--libraries)
- [Core Features & Modules](#core-features--modules)
- [Folder Structure](#folder-structure)
- [Installation & Setup Guide](#installation--setup-guide)
- [Administrative Access](#administrative-access)
- [Testing & Verification](#testing--verification)
- [Project Presentation & Prototype](#project-presentation--prototype)
- [License](#license)

---

## Technical Stack & Libraries

| Layer | Technology |
|-------|-----------|
| **Core Framework** | Django 5.x, Python 3.14.6 (Python 3.10+ supported) |
| **Database** | SQLite (Development) |
| **Frontend & Styling** | Vanilla CSS, Bootstrap 5, Font Awesome, Chart.js (CDN) |
| **Document Exporting** | ReportLab (PDF), openpyxl (Excel) |
| **Asset Utility** | qrcode (SVG vector generation) |
| **Authentication** | Custom User model using email as login identifier |

---

## Core Features & Modules

### 1. Role-Based Authentication & Profiles
- **Custom User Model**: Extends Django's `AbstractUser` to log in via `email` instead of `username`, adding `full_name`, `role` (`admin` or `student`), `phone_number`, `profile_image`, and contact `address`.
- **User Profile Page**: Edit full name, address, contact number, upload a profile avatar, and change password. Logged-in users see their avatar dynamically in the top header.
- **Login Auditing**: Authentication signals automatically log user logins and logouts in the system activity feed.

### 2. Department & Equipment Manager
- **Department CRUD**: Create, edit, list, and delete departments with codes and descriptions.
- **Equipment CRUD**: Track physical assets with sequentially generated codes (e.g. `EQ0001`), manufacturer, model number, cost, condition, available/total stock count, location, status, and image files.
- **Auto Status Adjustments**: Equipment status switches to `Out of Stock` when `available_quantity == 0` and resets to `Available` on replenishment.

### 3. Equipment Booking (Lending) Module
- **Reservation Workflow**: Students submit requests with quantity, expected return date, and purpose.
- **Stock Guard Checking**: Blocks requests when the requested quantity exceeds current available stock.
- **Duplicate Request Block**: Prevents students from creating duplicate active requests for the same item.
- **Automated Stock Adjustments**: Decrements inventory on admin approval, records return timestamps, and increments stock back on return.

### 4. Damage Reporting System
- **Damage Reports**: Students file reports describing cracks, broken parts, and severity level (`Low`, `Medium`, `High`, `Critical`) with photo proof.
- **Constraint Check**: Reports can only be filed on items the student has returned (a booking in `Returned` status).
- **Admin Review**: Admins review, search, filter, and resolve reports by adding resolution remarks.

### 5. Automated Notification Alerts & Low Stock Warnings
- **Global Notification Bell**: Header dropdown showing live unread counts and recent alerts, with AJAX triggers to mark alerts as read.
- **Low Stock Triggers**: Automatically notifies all admins when available stock drops to `2` or fewer.

### 6. Document Exports & QR Code Generator
- **ReportLab PDFs**: Professional PDF reports with college headers, page counts ("Page X of Y"), and styled data grids.
- **Excel Exports**: Streams openpyxl spreadsheets with styled title blocks, bordered grids, column filters, and auto-adjusted widths.
- **QR Code Utility**: Dynamically generates vector SVG QR codes containing the equipment code, name, department, and location, with inline viewing and file download.

---

## Folder Structure

```text
Lab-Inventory-Management-System/
│
├── LabInventorySystem/       # Main Django settings and URL routing
│   ├── settings.py           # Database configs, template processors and auth setup
│   ├── urls.py               # Main URL declarations
│   └── wsgi.py
│
├── accounts/                 # Registration, profiles and user authentication
│   ├── forms.py              # Profile and register forms with password validation
│   ├── models.py             # Custom User model definition (email login)
│   ├── urls.py
│   └── views.py
│
├── inventory/                # Department & Equipment catalogs
│   ├── admin.py              # Previews, actions and hierarchy configuration
│   ├── models.py             # Department, Equipment models & QR generators
│   ├── forms.py              # File upload and validation structures
│   ├── urls.py
│   └── views.py
│
├── bookings/                 # Loan bookings and damage reports
│   ├── models.py             # Booking and DamageReport models
│   ├── forms.py
│   ├── urls.py
│   └── views.py
│
├── dashboard/                # Activity feeds, notifications and system configuration
│   ├── context_processors.py # Injects alerts and settings globally
│   ├── models.py             # Notification, ActivityLog, SystemSettings models
│   ├── signals.py            # Listens to logins/logouts for auditing
│   ├── forms.py              # SystemSettingsForm validations
│   ├── urls.py
│   └── views.py
│
├── scratch/                  # Developer utilities and verification scripts (verify.py)
├── static/                   # Static CSS styles and JavaScript scripts
├── templates/                # HTML layout templates styled with Bootstrap 5
├── media/                    # Uploaded files (created at runtime: avatars, equipment images, branding)
│
├── index.html                # First prototype file (static UI prototype)
├── Lab Equipment Booking & Management Sys...   # Project presentation slides
├── requirements.txt          # Library dependencies
├── manage.py
├── LICENSE
└── README.md                 # Project documentation
```

---

## Installation & Setup Guide

### 1. Prerequisites
Ensure you have **Python 3.10+** and **Git** installed on your computer.

### 2. Clone the Repository
```bash
git clone <your-repository-url>
cd <repository-folder>
```

### 3. Set Up a Virtual Environment
From the project root:
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Windows CMD)
.venv\Scripts\activate.bat

# Activate (macOS/Linux)
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Apply Database Migrations
Create the database tables and schemas:
```bash
python manage.py makemigrations accounts inventory bookings dashboard
python manage.py migrate
```

### 6. Run the Local Server
```bash
python manage.py runserver
```
The application will be available at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## Administrative Access

For evaluation, the following credentials are pre-configured in the bundled development database:

| Field | Value |
|-------|-------|
| **Admin Email** | `admin@lab.com` |
| **Admin Password** | `adminpassword123` |

> **Note:** These credentials are for local development and evaluation only. Change them (or create a fresh admin account) before deploying anywhere public.

If your copy of the database does not include this account, create one from the command line:
```bash
python manage.py createsuperuser
```

---

## Testing & Verification

Run the test suite to verify that all modules are operational:
```bash
# Runs 48 unit tests covering validations, model constraints, and downloads
python manage.py test

# Runs custom integration verification checks
python scratch/verify.py
```

---

## Project Presentation & Prototype

- **Slides**: The repository includes the project presentation (*Lab Equipment Booking & Management System*) describing the problem, design, and workflow.
- **Prototype**: `index.html` is the first static prototype of the interface, kept for reference. Open it directly in a browser; it does not require the Django server.

---

## License

This project is distributed under the terms of the license included in the [LICENSE](LICENSE) file.
