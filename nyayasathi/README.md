# NS-BE (NyayaSathi Backend)

A Django REST API backend for the NyayaSathi legal assistance platform.

## Features

- **RESTful API**: Built with Django REST Framework
- **User Authentication**: Custom user model with token authentication
- **Complaint Management**: Submit and track legal complaints
- **AI Integration**: Groq API for legal document processing
- **File Upload**: Handle document uploads and processing
- **CORS Support**: Cross-origin resource sharing for frontend integration
- **Production Ready**: Configured for Render deployment

## Tech Stack

- **Framework**: Django 5.2.3
- **API**: Django REST Framework 3.14.0
- **Database**: PostgreSQL (production), SQLite (development)
- **Authentication**: Token-based authentication
- **AI Services**: Groq API, Hugging Face
- **Deployment**: Render

## Project Structure

```
nyayasathi/
├── complaints/          # Main app for complaint management
│   ├── models.py       # Custom user and complaint models
│   ├── views.py        # API views and endpoints
│   ├── serializers.py  # Data serialization
│   ├── urls.py         # URL routing
│   └── utils.py        # Utility functions
├── nyayasathi/         # Django project settings
│   ├── settings.py     # Development settings
│   ├── production.py   # Production settings
│   ├── urls.py         # Main URL configuration
│   └── wsgi.py         # WSGI application
├── requirements.txt    # Python dependencies
├── build.sh           # Render build script
├── manage.py          # Django management script
└── env.example        # Environment variables template
```

## API Endpoints

### Authentication
- `POST /api/register/` - User registration
- `POST /api/login/` - User login
- `POST /api/logout/` - User logout

### Complaints
- `GET /api/complaints/` - List user complaints
- `POST /api/complaints/` - Create new complaint
- `GET /api/complaints/{id}/` - Get complaint details
- `PUT /api/complaints/{id}/` - Update complaint
- `DELETE /api/complaints/{id}/` - Delete complaint

### File Processing
- `POST /api/upload/` - Upload legal documents
- `POST /api/summarize/` - Summarize legal documents
- `POST /api/chatbot/` - Legal chatbot interface

## Getting Started

### Prerequisites

- Python 3.8+
- pip
- PostgreSQL (for production)

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/varna8104/NS-BE.git
cd NS-BE/nyayasathi
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your actual values
```

5. Run database migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Django Settings
SECRET_KEY=your-django-secret-key-here
DEBUG=True

# API Keys
GROQ_API_KEY=your-groq-api-key-here
HUGGINGFACE_API_KEY=your-huggingface-api-key-here

# Database (for production)
DATABASE_URL=postgresql://user:password@host:port/database
```

## Deployment on Render

### Prerequisites

1. Render account
2. PostgreSQL database on Render
3. GitHub repository connected

### Deployment Steps

1. **Create a new Web Service** on Render
2. **Connect your GitHub repository**: `varna8104/NS-BE`
3. **Configure the service**:
   - **Name**: `ns-be` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn nyayasathi.wsgi:application`
   - **Root Directory**: `nyayasathi`

4. **Add Environment Variables**:
   - `SECRET_KEY`: Your Django secret key
   - `DATABASE_URL`: Render PostgreSQL URL
   - `GROQ_API_KEY`: Your Groq API key
   - `HUGGINGFACE_API_KEY`: Your Hugging Face API key
   - `DEBUG`: `False`

5. **Deploy** - Render will automatically build and deploy your application

### Build Configuration

The `build.sh` script handles:
- Installing dependencies
- Collecting static files
- Running database migrations

## API Documentation

### Authentication

All API endpoints require authentication except registration and login.

Include the token in the Authorization header:
```
Authorization: Token your-token-here
```

### Example API Calls

#### Register a new user:
```bash
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "password123"}'
```

#### Login:
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "password123"}'
```

#### Create a complaint:
```bash
curl -X POST http://localhost:8000/api/complaints/ \
  -H "Authorization: Token your-token-here" \
  -H "Content-Type: application/json" \
  -d '{"title": "Legal Issue", "description": "Description here"}'
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is part of the NyayaSathi legal assistance platform. 