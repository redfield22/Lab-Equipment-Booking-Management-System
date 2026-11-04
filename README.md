# Lab Equipment Booking & Management System

A browser-based laboratory equipment management prototype built using HTML5, CSS3, and Vanilla JavaScript.

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

### 1. Equipment Inventory
- **Equipment Listing:** Displays equipment name, ID, category, quantity, location, and availability status.
- **Search:** Filter equipment by name, category, or location.
- **Add Equipment:** Lab Staff can add equipment to the inventory with its basic details.
- **Availability Status:** Equipment can be marked as available or under maintenance.

### 2. Equipment Booking
- **Booking Requests:** Students can select equipment, enter their details, choose a booking date and quantity, and provide a purpose.
- **Quantity Validation:** Prevents requests for quantities greater than the listed inventory quantity.
- **Request Status:** New requests are recorded as `Pending`.
- **Staff Review:** Lab Staff can approve or reject pending requests.

### 3. Equipment Issue & Return
- **Issue Recording:** Staff can record the issue of approved equipment.
- **Stock Updates:** The available quantity is reduced when equipment is issued.
- **Return Recording:** Staff can record when equipment is returned.
- **Return Inspection:** Staff can flag returned equipment for maintenance or return it to available stock.

### 4. Maintenance Management
- **Maintenance Records:** Staff can record equipment maintenance notes.
- **Unavailable Equipment:** Equipment under maintenance cannot be requested.
- **Repair Completion:** Staff can close a maintenance record and mark the equipment available again.

### 5. Dashboard
- **Summary Cards:** Shows equipment types, available units, pending booking requests, and equipment under maintenance.
- **Recent Activity:** Displays recent booking activity.
- **Quick Navigation:** Provides shortcuts to inventory, bookings, and equipment operations.

### 6. Demonstration Roles
- **Student View:** Browse equipment and submit booking requests.
- **Lab Staff View:** Add equipment, review requests, issue and return equipment, and manage maintenance.
- **Demo Role Switch:** Switches between the two views for demonstration. It is not a real authentication system.

---

## Folder Structure

```text
lab-equipment-booking-management-system/
│
├── assets/
│   └── images/             # Images used by the project
│
├── css/
│   └── styles.css          # Application styles and responsive layout
│
├── docs/
│   ├── diagrams/           # Exported DFD and UML diagrams
│   └── README-structure.md # Notes about the project structure
│
├── js/
│   ├── app.js              # Application entry point and page interactions
│   ├── state.js            # Sample data and LocalStorage operations
│   ├── utils.js             # Shared helper functions
│   ├── inventory.js        # Equipment inventory functions
│   ├── bookings.js         # Booking request and approval functions
│   └── operations.js       # Issue, return, and maintenance functions
│
├── screenshots/            # Screenshots of the running prototype
├── index.html              # Main application page
├── .gitignore
└── README.md
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
