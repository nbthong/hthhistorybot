# hthhistoryAIAssisstant
# ReactJS + FastAPI + Docker

A **minimal, lightweight, and production-ready assisstant template** using:

- **ReactJS** for the frontend
- **FastAPI** for the backend API
- 🐳 **Docker & Docker Compose** for easy local development and deployment

---

## Project Structure

```
.
├── backend/
│   ├── app              
│   │   └── main.py   # FastAPI app
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Backend Docker image
├── frontend/
│   ├── src/
│   │   └── App       # Main UI
│   ├── index.html
│   ├── package.json
│   └── Dockerfile           # Frontend Docker image
├── docker-compose.yml       # Run frontend + backend
└── README.md
