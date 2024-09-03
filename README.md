
# Redis-Pro-Maxx

## Project Overview

**Redis-Pro-Maxx** is a Python-based task distribution system designed to efficiently manage and distribute tasks to dynamically created worker processes. The system automatically scales the number of workers based on the current load, ensuring optimal resource usage and cost efficiency. This self-contained application stores all its data internally, making it a robust and efficient solution for dynamic task management.

## Motivation

In many systems, handling fluctuating workloads while maintaining efficiency and cost-effectiveness can be challenging. Traditional load balancers distribute tasks but often require manual intervention or external systems to manage worker processes. DPLB addresses this challenge by automatically scaling worker processes in response to the load, ensuring that resources are used effectively without unnecessary overhead. This makes it an ideal solution for environments where workloads are highly variable and need to be managed in real-time.

## Technologies Used

- **Python**: Core language for the entire application.
- **Flask**: Used as the web framework to create a lightweight API for task submission and monitoring.
- **Docker**: Containerization tool to ensure that the application can run consistently across different environments.
- **AWS**: Deployment platform, providing scalable cloud infrastructure for running the application.
- **GitHub Actions**: CI/CD pipeline for automated testing, building, and deployment of the application.


## Features

- **Dynamic Worker Creation and Auto-Scaling**: Automatically adjusts the number of worker processes based on the current load.
- **Task Distribution**: Efficiently distributes incoming tasks to available workers.
- **Self-Contained Data Management**: All data is stored within the application, eliminating the need for external databases.
- **Dockerized Deployment**: Easily deploy the application using Docker, ensuring consistency across environments.
- **CI/CD with GitHub Actions**: Automated testing, building, and deployment to ensure code quality and streamline updates.

## Installation and Setup

### Prerequisites

- Python 3.8+
- Docker
- AWS CLI (for deployment to AWS)
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/dplb.git
cd dplb
```

### Step 2: Set Up a Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

Install the required Python packages.

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the root directory and add the necessary environment variables. Example:

```plaintext
FLASK_APP=app.py
FLASK_ENV=production
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### Step 5: Run the Application Locally

```bash
flask run
```

The application should now be running at `http://127.0.0.1:5000/`.

### Step 6: Dockerize the Application

Build and run the Docker container.

```bash
docker build -t dplb .
docker run -p 5000:5000 dplb
```

### Step 7: Deploy to AWS

1. **AWS Setup:** Ensure you have your AWS CLI configured with the necessary IAM permissions.

2. **Push Docker Image to AWS ECR:**

```bash
aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com
docker tag dplb:latest your-account-id.dkr.ecr.your-region.amazonaws.com/dplb:latest
docker push your-account-id.dkr.ecr.your-region.amazonaws.com/dplb:latest
```

3. **Deploy Using AWS ECS or Fargate:**
   - Create an ECS or Fargate cluster.
   - Define a task with the Docker image.
   - Deploy the service.

### Step 8: Set Up CI/CD with GitHub Actions

This project includes a `.github/workflows/main.yml` file for GitHub Actions. The pipeline is configured to:

- Run tests on push.
- Build and push the Docker image to AWS ECR.
- Deploy the latest version to AWS.

To set up GitHub Actions:

1. Create secrets in your GitHub repository for AWS credentials:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`
   - `ECR_REPOSITORY`

2. Push your code to GitHub. The CI/CD pipeline will automatically run.

## API Endpoints

The following endpoints are available in the application:

- **POST /tasks**: Submit a new task to the load balancer.
- **GET /tasks/<id>**: Retrieve the status of a specific task.
- **GET /workers**: Get the current status of worker processes.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss any changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Contact

For any questions or support, please reach out to [your-email@example.com](mailto:your-email@example.com).
