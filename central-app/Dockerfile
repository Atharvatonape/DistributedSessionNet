FROM python:3.9-slim

# Install curl
RUN apt-get update && apt-get install -y curl
RUN apt-get update && apt-get install -y net-tools


WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]