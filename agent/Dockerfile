FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Copy only dependency files first to leverage Docker layer caching
COPY pyproject.toml uv.lock* ./

# Install uv and sync dependencies
RUN pip install --no-cache-dir uv && \
    uv sync --no-cache

# Copy the rest of the application code
COPY . .

# Remove .env file if it exists to avoid leaking sensitive information
RUN rm -rf .env 

ENV PORT=8080
EXPOSE 8080

# Use the shell form of CMD to allow for environment variable substitution
CMD uv run streamlit run app_streamlit.py --server.port=$PORT --server.address=0.0.0.0