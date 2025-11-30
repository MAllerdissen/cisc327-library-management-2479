# Use an official lightweight Python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install Python dependencies
# (Assumes requirements.txt is in the project root)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code, including library.db
COPY . .

# Configure Flask to use the application factory in app.py
ENV FLASK_APP=app:create_app

# Expose port 5000 inside the container
EXPOSE 5000

# Run the Flask development server on port 5000, accessible from outside
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
