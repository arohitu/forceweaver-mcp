# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY . .

# Create a non-root user to run the application
RUN addgroup --system app && adduser --system --group app
RUN chown -R app:app /usr/src/app
USER app

# Expose port
EXPOSE 8080

# Run the app using a production-ready WSGI server like Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "--workers", "4", "--timeout", "120", "app:create_app()"]