# Tournament Info Backend

Backend API for a tournament management platform built with Django and Django REST Framework.

## Tech Stack

- Python
- Django 4.2.28
- Django REST Framework 3.15.2
- MySQL
- JWT (SimpleJWT)
- Boto3 / django-storages
- Amazon EC2
- Amazon RDS
- Amazon S3
- Gunicorn

## Database
<img width="977" height="1147" alt="image" src="https://github.com/user-attachments/assets/87a79036-f888-41c8-a6d0-a1e350401a43" />


## Features

### Authentication & Users

- User registration and login
- JWT authentication
- Access / Refresh tokens
- Role-based users
  - `PLAYER`
  - `SHOP_OWNER`
- User balance management

### Shops

- Shop management
- One-to-one relationship between users and shops
- Shop owner authorization

### Tournaments

- Tournament creation, list, detail, and update
- Tournament status management
- Tournament cancellation and refund
- Tournament pagination
- Owner-only tournament management
- Multiple game types
  - Poker
  - Chess
  - Pokémon TCG
  
### Poker Tournaments

- Entry / re-entry / add-on limits
- Starting chips and additional chips
- Re-entry / add-on fees
- Blind structure management
- Tournament statistics and cache fields

### Tournament Entries

- Player registration
- Entry approval
- Table / seat assignment
- Bust management
- Entry / re-entry / add-on tracking
- Buy-in event history
- Paginated entry management

### Images

- Multiple tournament images
- Primary image support
- Amazon S3 image storage
- Presigned URL access

## Architecture

```text
Client
  │
  ▼
EC2
Django + Gunicorn
  │
  ├── RDS (MySQL)
  │
  └── S3 (Tournament Images)
```
## API

The backend API is organized into separate modules for users, shops, and tournaments.

```text
/api/users/
/api/shops/
/api/tournaments/

Authentication

POST /api/users/signup/
POST /api/users/login/
GET  /api/users/me/

Tournament

GET   /api/tournaments/
GET   /api/tournaments/<id>/
PATCH /api/tournaments/<id>/edit/
PATCH /api/tournaments/<id>/status/

Shop Owner

GET /api/tournaments/my-shop-tournaments/<id>/
GET /api/tournaments/my-shop-tournaments/<id>/entries/

The shop owner APIs allow shop owners to manage their own tournaments
and view registered players with pagination.
```
## Local Development

```bash
git clone <repository-url>
cd tournament_info

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

The development server runs at:

http://127.0.0.1:8000/
```

## Environment Variables
Sensitive configuration is managed through environment variables.
```bash
SECRET_KEY=your-secret-key

DB_NAME=your-database-name
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_HOST=your-rds-endpoint
DB_PORT=3306

AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=ap-northeast-2
