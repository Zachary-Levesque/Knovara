.PHONY: dev-backend dev-frontend test-backend build-frontend audit-frontend

dev-backend:
	cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000

dev-frontend:
	cd frontend && npm run dev

test-backend:
	python -m pytest backend/test_api.py

build-frontend:
	cd frontend && npm run build

audit-frontend:
	cd frontend && npm audit
