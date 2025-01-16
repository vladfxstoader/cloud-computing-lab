# Microservices-Based Hotel Reservation System

This repository contains a **web application based on microservices** for a hotel reservation system. Each microservice is containerized using **Docker** and has its own database.

---

## Features

- **Microservices Architecture**: 
  - Independent services for user, hotel, room, reservation and payment management.
- **Frontend**: A dedicated frontend service to interact with the backend microservices.
- **Scalability**: Manual scaling supported through Docker Swarm.
- **Observability**:
  - **Metrics**: Prometheus integration for performance monitoring.
  - **Tracing**: Jaeger for distributed tracing across microservices.
  - **Logging**: Centralized logging via Rsyslog.
- **API Gateway**: NGINX for load balancing and routing requests to appropriate services.

---

## Architecture Overview

### Microservices

| Service                  | Port  | Description                                      |
|--------------------------|-------|--------------------------------------------------|
| **user-service**         | 5000  | Manages user information and authentication.     |
| **hotel-service**        | 5001  | Handles hotel information and availability.      |
| **room-service**         | 5002  | Manages room details for hotels.                 |
| **reservation-service**  | 5003  | Handles booking and reservation logic.           |
| **payment-service**      | 5004  | Processes payments for reservations.             |
| **hotel-frontend**       | 8085  | Provides a user interface for interaction.       |

### Supporting Components

| Component       | Description                                      |
|------------------|-------------------------------------------------------|
| **Prometheus**    | Metrics monitoring and alerting.                |
| **Jaeger**        | Distributed tracing of microservice requests.    |
| **NGINX**        | Load balancer and API Gateway.                  |
| **Rsyslog**        | Centralized logging for all microservices.       |

---

## Prerequisites

- Docker


---

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/vladfxstoader/cloud-computing-lab.git
cd hotel-reservations
```
### 2. Build and Run the Application
```bash
docker swarm init

docker build -t user-service:latest ./user-service
docker build -t hotel-service:latest ./hotel-service
docker build -t room-service:latest ./room-service
docker build -t reservation-service:latest ./reservation-service
docker build -t payment-service:latest ./payment-service
docker build -t notification-service:latest ./notification-service
docker build -t hotel-frontend:latest ./frontend-service
docker build -t rsyslog-server:latest .

docker stack deploy -c docker-compose.yml hotel-app
```
### 3. Access the Application
- Frontend: http://localhost:8085
- Prometheus Dashboard: http://localhost:9090
- Jaeger UI: http://localhost:16686
  
### 4. Stop the Application
```bash
docker stack rm hotel-app
docker swarm leave
```
---
## Contributors

- [Predescu Denisa](https://github.com/denisapredescu)
- [Sandu Raluca](https://github.com/ralucsandu)
- [Toader Vlad](https://github.com/vladfxstoader)
