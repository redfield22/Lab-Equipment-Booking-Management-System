# Lab Equipment Booking & Management System

A browser-based laboratory equipment management system prototype built using HTML5, CSS3, and Vanilla JavaScript.

Designed to demonstrate how a lab can manage equipment inventory, receive booking requests, approve reservations, record equipment issue and return, and track maintenance activity through a simple interface.

---

## Technical Stack & Libraries

- **Structure:** HTML5
- **Styling:** CSS3 (Grid, Flexbox, media queries, custom properties)
- **Application Logic:** Vanilla JavaScript (ES modules)
- **Browser APIs:** DOM API, FormData, LocalStorage
- **Data Format:** JavaScript objects and JSON serialization
- **Development Tools:** Visual Studio Code, Git, GitHub

No frontend framework, backend framework, or database server is used. The prototype stores its demonstration data in the browser's LocalStorage.

---

## Core Features & Modules

### 1. Equipment Inventory (`equipment/`)
- **Equipment Listing**: Displays equipment name, ID, category, quantity, location, and availability status from the models.
- **Search**: Filters equipment by name, category, or location.
- **Add Equipment**: Lab Staff can add equipment with its basic details through the admin interface, which provides previews, actions, and hierarchy configuration.
- **Availability Status**: Stores whether equipment is available or under maintenance.

### 2. Equipment Booking (`reservations/`)
- **Booking Requests**: Students select equipment, enter their details, choose a booking date and quantity, and provide a purpose.
- **Quantity Validation**: Prevents requests for quantities greater than the inventory quantity.
- **Request Status**: The `Booking` model records new requests as `Pending`.
- **Staff Review**: Lets Lab Staff approve or reject pending requests.

### 3. Equipment Issue & Return (`reservations/` + `equipment/`)
- **Issue Recording**: Lets staff record the issue of approved equipment.
- **Stock Updates**: Reduces the available quantity when equipment is issued.
- **Return Recording**: Lets staff record when equipment is returned.
- **Return Inspection**: Staff can flag returned equipment for maintenance by creating a `DamageReport`, or return it to available stock.

### 4. Maintenance Management (`equipment/` + `reservations/`)
- **Maintenance Records**: Staff record maintenance notes, linked to a `DamageReport`.
- **Unavailable Equipment**: Equipment marked as under maintenance cannot be requested.
- **Repair Completion**: Lets staff close a maintenance record and mark the equipment available again.

### 5. Dashboard (`monitoring/`)
- **Summary Cards**: Shows equipment types, available units, pending booking requests, and equipment under maintenance.
- **Recent Activity**: `ActivityLog` and `Notification` records feed the recent booking activity display, with signals recording logins and logouts for auditing.
- **Quick Navigation**: Provides shortcuts to inventory, bookings, and equipment operations, with alerts and settings injected globally through a context processor.

### 6. Demonstration Roles (`users/`)
- **Student View**: Browse equipment and submit booking requests.
- **Lab Staff View**: Add equipment, review requests, issue and return equipment, and manage maintenance.
- **Demo Role Switch**: Switches between the two views for demonstration. It is not a real authentication system, even though the project defines a custom `User` model with email login.
---

## Folder Structure

```text
LabEquipmentTracker/
│
├── core_config/              # Main Django settings and URL routing
│   ├── config.py             # Database configs, template processors and auth setup
│   ├── routes.py             # Main URL declarations
│   └── server_gateway.py
│
├── users/                    # Registration, profiles and user authentication
│   ├── user_forms.py         # Profile and register forms with password validation
│   ├── user_models.py        # Custom User model definition (email login)
│   ├── routes.py
│   └── user_views.py
│
├── equipment/                # Department & Equipment catalogs
│   ├── admin_panel.py        # Previews, actions and hierarchy configuration
│   ├── entities.py           # Department, Equipment models & QR generators
│   ├── input_forms.py        # File upload and validation structures
│   ├── routes.py
│   └── handlers.py
│
├── reservations/             # Loan bookings and damage reports
│   ├── entities.py           # Booking and DamageReport models
│   ├── input_forms.py
│   ├── routes.py
│   └── handlers.py
│
├── monitoring/               # Activity feeds, notifications and system configuration
│   ├── global_context.py     # Injects alerts and settings globally
│   ├── entities.py           # Notification, ActivityLog, SystemSettings models
│   ├── event_listeners.py    # Listens to logins/logouts for auditing
│   ├── input_forms.py        # SystemSettingsForm validations
│   ├── routes.py
│   └── handlers.py
│
├── dev_tools/                # Developer utilities and verification scripts (check_setup.py)
├── assets/                   # Static CSS styles and JavaScript scripts
├── layouts/                  # HTML layout templates styled with Bootstrap 5
├── uploads/                  # Uploaded files (created at runtime: avatars, equipment images, branding)
│
├── prototype.html            # First prototype file (static UI prototype)
├── Lab Equipment Booking & Management Sys...   # Project presentation slides
├── LICENSE
└── README.md                 # Project documentation
```

---

## Installation & Setup Guide

### 1. Prerequisites

- A modern web browser
- Python 3 installed (for the local development server)

### 2. Download the Project

Clone the repository:

```bash
git clone <your-repository-url>
cd lab-equipment-booking-management-system
```

### 3. Start the Local Server

Run this command from the project root:

```bash
python3 -m http.server 8000
```

### 4. Open the Application

Visit:

```text
http://localhost:8000
```

JavaScript ES modules are used, so run the project through a local web server instead of opening `index.html` directly using `file://`.

---

## Demo Workflow

1. Open the **Inventory** tab and browse the sample equipment.
2. Use **Demo as Student** to submit a booking request.
3. Switch to **Demo as Lab Staff** to approve or reject the request.
4. Open **Issue / Return & Maintenance** to record an equipment issue or return.
5. Add a maintenance record and mark the repair complete.

---

## Data Storage & Limitations

- Demo data is stored in the browser's **LocalStorage**.
- Data remains in the same browser profile but is not shared between different users or devices.
- The role selector is a demonstration feature, not secure authentication.
- There is no backend server, database server, API, or server-side authorization.
- This is an academic frontend prototype. Do not enter real student or institutional information.

---

## Future Enhancements

- Backend integration using Django, Flask, or Node.js.
- Central database for equipment, users, and booking records.
- Secure login with role-based authorization.
- Multi-user access and synchronized booking data.
- Email or in-app notifications.
- Equipment QR codes and downloadable inventory reports.

---

## Project Status

**Academic prototype — frontend demonstration.**

The current version demonstrates the main equipment lifecycle through a browser interface. Backend services, institutional authentication, and centralized database functionality are not included.
