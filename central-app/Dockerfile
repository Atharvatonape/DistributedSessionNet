
FROM python:3.8
WORKDIR /app
 # Install system dependencies in one layer to keep it clean and efficient
RUN apt-get update && apt-get install -y \
curl \
net-tools \
iputils-ping \
&& rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]
 
