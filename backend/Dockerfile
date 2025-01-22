FROM python:3.10-slim

# Set environment variables to prevent Python from generating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y git mesa-gl && apt-get clean

# Set the working directory
WORKDIR /app

# Copy requirements file to the container
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code to the container
COPY . .

# Expose the application port
EXPOSE 8000

# Command to run the FastAPI app
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
