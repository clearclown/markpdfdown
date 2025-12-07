FROM python:3.9-slim

WORKDIR /app

# Install dependencies for PDF processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY core/ ./core/
COPY main.py ./

# Install base dependencies
RUN pip install --no-cache-dir -e .

# Install Gemini support (optional but recommended)
RUN pip install --no-cache-dir google-genai || true

CMD ["python", "main.py"]
