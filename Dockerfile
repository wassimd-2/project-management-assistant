# Use an official, stable Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy just the requirements file first to leverage Docker's caching
COPY requirements.txt .

# Install dependencies (no-cache-dir keeps the image size small)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application codebase into the container
COPY . .

# Expose the default Streamlit port
EXPOSE 8501

# Command to run the Streamlit dashboard on container startup
CMD ["streamlit", "run", "ui/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]