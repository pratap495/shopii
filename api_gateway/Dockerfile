# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on (Defaulting to 8000, change as needed)
EXPOSE 8000

# Set environment variables to ensure output is sent to logs
ENV PYTHONUNBUFFERED=1

# Command to run the application (Replace 'main.py' with your actual entry file)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]