# docker/Dockerfile.app
# FROM python:3.12-slim

# ENV PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1

# RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# WORKDIR /app
# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt

# # Copie tout (l'app lit les endpoints API et users.json)
# COPY . .

# EXPOSE 8501
# HEALTHCHECK --interval=20s --timeout=3s --retries=5 \
#   CMD curl -fsS http://localhost:8501/_stcore/health >/dev/null || exit 1

# # Démarrage Streamlit
# CMD ["python","-m","streamlit","run","app/app_simple.py","--server.port=8501","--server.address=0.0.0.0"]

# docker/Dockerfile.app
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["python","-m","streamlit","run","app/app_simple.py","--server.port=8501","--server.address=0.0.0.0"]
