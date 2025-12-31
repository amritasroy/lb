.PHONY: help install train test run docker-build docker-run clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

train: ## Train the model with sample data
	python train.py --data-path sample_data.csv --artifacts-dir ./artifacts

test: ## Run test script
	python test_model.py

run: ## Run the service locally
	uvicorn app:app --host 0.0.0.0 --port 8000 --reload

run-prod: ## Run the service with Gunicorn (production mode)
	./start.sh

docker-build: ## Build Docker image
	docker build -t churn-model:latest .

docker-run: ## Run Docker container locally
	docker run -p 8000:8000 -v $(PWD)/artifacts:/app/artifacts churn-model:latest

k8s-deploy: ## Deploy to Kubernetes
	kubectl apply -f deployment.yaml

k8s-delete: ## Delete Kubernetes deployment
	kubectl delete -f deployment.yaml

k8s-logs: ## Show Kubernetes logs
	kubectl logs -f -l app=churn-model

clean: ## Clean generated files
	rm -rf artifacts/
	rm -rf __pycache__/
	rm -rf *.pyc
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +

zip: clean ## Create submission ZIP file
	zip -r mlzone-churn-model.zip . -x "*.git*" -x "*__pycache__*" -x "*.pyc" -x "artifacts/*"
	@echo "Created mlzone-churn-model.zip"
