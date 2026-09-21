import os

# Render dynamically assigns a PORT environment variable.
# Binding to 0.0.0.0:$PORT ensures Render port detection succeeds when running 'gunicorn app:app'.
port = os.environ.get('PORT', '5000')
bind = f'0.0.0.0:{port}'

# Generous timeout for initial SentenceTransformer/FAISS cold-start loading
timeout = 120

# Single worker by default to stay within memory limits for ML models
workers = int(os.environ.get('WEB_CONCURRENCY', '1'))
