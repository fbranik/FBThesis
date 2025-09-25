# Use the official Python image as a base
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file to the working directory
COPY . /app

# Install the required dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 4100

# Define the command to run the app and expose the port the app runs on
CMD ["gunicorn", "--bind", "0.0.0.0:4100", "main:dashApp"] 
