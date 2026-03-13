# Use Python 3.11 slim image from public registry
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only necessary application files
COPY app.py .
COPY rag_pipeline.py .
COPY ingestion.py .
COPY policy_corpus/ ./policy_corpus/

# Create vector db directory (empty - will be populated at runtime)
RUN mkdir -p nsr_vector_db

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Run ingestion first, then start the app
CMD ["sh", "-c", "python ingestion.py && python app.py"]
