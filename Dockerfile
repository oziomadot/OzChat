# Build stage
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements-minimal.txt requirements.txt

# Install dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy only necessary application files
COPY app.py .
COPY rag_pipeline_lite.py .
COPY ingestion_lite.py ingestion.py
COPY policy_corpus/ ./policy_corpus/

# Create vector db directory (empty - will be populated at runtime)
RUN mkdir -p nsr_vector_db

# Clean up to reduce size
RUN rm -rf /usr/local/lib/python3.11/site-packages/*/tests && \
    rm -rf /usr/local/lib/python3.11/site-packages/*test* && \
    find /usr/local/lib/python3.11/site-packages -name "*.pyc" -delete && \
    find /usr/local/lib/python3.11/site-packages -name "*.pyo" -delete

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Run ingestion first, then start the app
CMD ["sh", "-c", "python ingestion.py && python app.py"]
