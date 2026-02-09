# Tournament_Info

Webservice for poker tournament based on Django

---

## Tech Stack

- Python 3.8.11
- Django 4.2.28
- MySQL
- Django REST Framework 3.15.2
- AWS S3

---

## Core Features

### All Users
- SignUp / Distinguish between players and stores
- Tournaments list view

### Players
- Entries into the tournament
- Entry fee payments

### Store
- Creating and managing tournaments
- Managing live tournaments

---

## Database

- users
- shops
- tournaments
- tournament_entries
- tournament_images (S3)

---

## Environment Setup

### Create and activate virtual environments
```bash
python -m venv venv
source venv/bin/activate
