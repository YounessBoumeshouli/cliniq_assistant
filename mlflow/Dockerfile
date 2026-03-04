FROM python:3.11-slim

RUN pip install mlflow psycopg2-binary

WORKDIR /mlflow

EXPOSE 5000

CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000", "--backend-store-uri", "sqlite:///mlflow/mlflow.db", "--default-artifact-root", "/mlflow/artifacts", "--allowed-hosts", "*"]