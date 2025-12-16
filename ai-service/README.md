# MedAssist AI Service

AI microservice for intelligent patient communication and clinical insights.

## Project Structure

```
ai-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── models/              # Pydantic schemas
│   │   ├── __init__.py
│   │   └── schemas.py       # Request/response models
│   ├── services/            # AI logic modules
│   │   └── __init__.py
│   └── utils/               # Helper functions
│       └── __init__.py
├── tests/                   # Test suite
│   └── __init__.py
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
cd ai-service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Run the Service

```bash
# Development mode with auto-reload
python app/main.py

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## API Endpoints

### Health Check
- `GET /health` - Service health status
- `GET /api/v1/health` - API health status

### Message Processing (Coming Soon)
- `POST /api/v1/message/process` - Process patient messages

### Symptom Reports (Coming Soon)
- `POST /api/v1/symptom/report` - Generate symptom reports

## Development

### Running Tests
```bash
pytest tests/ -v --cov=app
```

### Code Formatting
```bash
black app/ tests/
flake8 app/ tests/
```

### Type Checking
```bash
mypy app/
```

## Current Status

✅ **Task 1 Completed:** Project structure initialized
- FastAPI application setup
- Configuration management
- Pydantic schemas defined
- Health check endpoints
- Development environment ready

## Next Steps

- Task 2: Implement intent classification module
- Task 3: Build slot filling and conversation manager
- Task 4: Develop symptom intake AI workflow

## Tech Stack

- **Framework:** FastAPI 0.109.0
- **AI/ML:** PyTorch 2.1.2, Transformers 4.36.2, LangChain 0.1.0
- **Validation:** Pydantic 2.5.3
- **Caching:** Redis 5.0.1
- **Testing:** pytest 7.4.4

## License

Proprietary - MedAssist Project
