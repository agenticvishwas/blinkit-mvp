# Dockerfile for the api/ FastAPI service (docs/phases/phase-4-deploy), built for
# Hugging Face Spaces' Docker SDK. Only agent/, api/, data/, and requirements.txt
# go into the image -- web/, docs/, design/ etc. are irrelevant to this service
# and excluded via .dockerignore to keep the build context small.
FROM python:3.12-slim

# HF Spaces runs containers as a non-root user by convention (UID 1000) --
# create one now so file ownership inside /app is correct from the start,
# rather than fighting permission errors at runtime.
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

# Install dependencies first (rarely changes) so Docker's layer cache is
# reused across rebuilds that only touch application code, keeping the
# 90s-ish cold sentence-transformers/torch install from re-running every push.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ ./agent/
COPY api/ ./api/
COPY data/ ./data/
RUN chown -R appuser:appuser /app

USER appuser

# HF Spaces' Docker SDK expects the app on port 7860 by default (also set
# explicitly via app_port in this repo's README.md frontmatter).
EXPOSE 7860

# CORS_ORIGINS and ANTHROPIC_API_KEY are read from the environment at runtime
# (agent/loop.py, api/main.py) -- set them as Space secrets/variables, never
# baked into the image.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
