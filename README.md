# VeriShield: AI-Powered Financial Identity Verification

VeriShield is an **open-source initiative** to build a **modular, scalable**, and **efficient** backend solution for **KYC (Know Your Customer)** and **KYB (Know Your Business)** processes. Leveraging technologies such as **FastAPI**, **PostgreSQL**, **Neo4j**, **Kafka**, and **Machine Learning**, the project automates identity verification, detects fraud, and provides risk scores—all while remaining flexible for community-driven enhancements.

---

## Table of Contents

1. [Introduction](#introduction)  
2. [Project Goals](#project-goals)  
   - [Core Objectives](#core-objectives)  
   - [Targeted Real-World Applications](#targeted-real-world-applications)  
3. [Features (Phase 1)](#features-phase-1)  
4. [Features (Phase 2)](#features-phase-2)  
5. [Quick Start (Docker-Only)](#quick-start-docker-only)  
6. [Testing (Docker-Only)](#testing-docker-only)  
7. [Seeding Data (Optional)](#seeding-data-optional)  
8. [Requirements](#requirements)  
9. [Project Structure](#project-structure)  
10. [Roadmap](#roadmap)  
11. [License](#license)  
12. [Contact](#contact)

---

## Introduction

VeriShield serves as a **backend simulation** for financial institutions, fintech startups, and e-commerce platforms seeking to streamline **KYC/KYB** processes. By automating verification, fraud detection, and risk scoring, it addresses complex identity management challenges in highly regulated sectors, providing:

- **Automated identity verification** to reduce manual checks and human error.  
- **Fraud detection** via advanced machine learning models.  
- **Real-time risk assessment** with event-driven architecture (Kafka).  
- **Graph-based analysis** (Neo4j) for revealing hidden relationships and suspicious patterns.

Ultimately, **VeriShield** forms a foundation for **community contributions** to drive innovation in identity verification and compliance.

---

## Project Goals

### Core Objectives

1. **Automate KYC/KYB** checks by validating user and business identities.  
2. **Detect anomalies and potential fraud** using machine learning.  
3. **Model and query entity relationships** in a graph database for advanced fraud detection.  
4. **Handle asynchronous workflows** with high reliability using **Kafka**.  
5. **Enable scalability** through containerization, microservices, and cloud readiness.

### Targeted Real-World Applications

- **Fintech**: Complying with AML (Anti-Money Laundering) rules, automating user identity checks for online banking, payments, etc.  
- **Digital Banking & E-Commerce**: Reducing fraudulent transactions in high-volume platforms.  
- **Fraud Detection**: Leveraging ML to detect suspicious patterns and preemptively flag high-risk activities.

---

## Features (Phase 1)

- **Dockerized Setup**: Quickly launch **FastAPI**, **PostgreSQL**, and **Neo4j** for local development.  
- **Basic Endpoint**: A `/health` route to confirm the service status.  
- **Initial Testing**: Simple Pytest coverage to ensure the environment is functional.  
- **Foundational Structure**: Clear directory layout, `.gitignore`, `.dockerignore`, and environment variables support.

---

## Features (Phase 2)

- **CRUD Endpoints**: Implemented **User** and **Business** create/read/update/verify endpoints with **FastAPI**.  
- **Database Integration**:  
  - **SQLAlchemy** models (`User`, `Business`) for PostgreSQL.  
  - Basic Neo4j driver setup for future graph enhancements.  
- **Secure Password Handling**:  
  - Passwords are stored as **hashed** strings (bcrypt via **Passlib**).  
  - Easy to expand for more advanced authentication flows.  
- **Expanded Testing**:  
  - Integration tests verifying CRUD endpoints (duplicates, not-found, success).  
  - Tests can now run **inside Docker** or locally.  
- **Seed Script**: A standalone `seed_data.py` (using **Faker**) to generate realistic user/business data, optionally seeding Neo4j.

With Phase 2, VeriShield transitions from a simple skeleton to a fully-functional RESTful backend for user/business management—paving the way for advanced features in upcoming phases (Kafka, ML, and deeper graph queries).

---

## Quick Start (Docker-Only)

Here’s a concise workflow to **spin up** VeriShield entirely in Docker (no local Python needed):

1. **Clone the Repo**  
   ```bash
   git clone https://github.com/Harshil7875/VeriShield-AI-Financial-Verification-Platform.git
   cd VeriShield-AI-Financial-Verification-Platform
   ```
2. **(Optional) Remove Obsolete `version:`**  
   - In `docker-compose.yml`, you might see `version: "3.9"`. For Docker Compose V2, it’s no longer needed.  
   - **Remove** or **comment out** that line to avoid the “obsolete” warning.

3. **Build & Start Containers**  
   ```bash
   docker compose up -d --build
   ```
   - **`-d`**: Detached mode (runs in the background).  
   - **`--build`**: Force-rebuild images from the Dockerfile.

4. **Check Container Status**  
   ```bash
   docker compose ps
   ```
   - Should show `backend` (FastAPI), `postgres` (healthy), and `neo4j` (running).

5. **Visit the Health Endpoint**  
   - Go to [http://localhost:8000/health](http://localhost:8000/health).  
   - Expected JSON: `{"status":"OK"}`

---

## Testing (Docker-Only)

All tests can be run **inside** the Docker container, eliminating any local environment quirks:

1. **Exec Into the Backend Container**  
   ```bash
   docker compose exec backend /bin/bash
   ```
   - Note: Here, `backend` is the **service name** in `docker-compose.yml`.

2. **Run Pytest**  
   ```bash
   pytest --cov=app --cov-report=term-missing
   ```
   - This runs all tests in the `/app/backend/tests` folder, connecting to Postgres (`host=postgres`) internally.  
   - You should see a passing test suite with coverage details.

3. **(Optional) Inspect Coverage Warnings**  
   - Common warnings: 
     - `MovedIn20Warning` (SQLAlchemy 2.0 changes)  
     - `DeprecationWarning` (Passlib crypt or Neo4j driver)  
   - These are not errors; future library upgrades will remove them.

---

## Seeding Data (Optional)

If you’d like to populate **Postgres** (and optionally **Neo4j**) with **dummy** users/businesses:

1. **Inside the Backend Container**  
   ```bash
   docker compose exec backend /bin/bash
   ```
2. **Run the Seed Script**  
   ```bash
   cd scripts
   python seed_data.py 10 15 True
   ```
   - **`10`**: Number of users to generate.  
   - **`15`**: Number of businesses to generate.  
   - **`True`**: Whether to also seed Neo4j.  
   - This also re-creates any missing tables, then inserts random data via **Faker**.

---

## Requirements

- **Docker Desktop** (or Docker Engine + Compose)  
- **Git** for version control  
- *(Optional)* **Python 3.11+** if you want to test or run scripts locally.  
- *(Optional)* **Conda/virtualenv** for local Python environment isolation.

> **Apple Silicon (M1/M2)**: The images used (`postgres:15`, `neo4j:5`, `python:3.11-slim-bullseye`) support `arm64`. If you face issues, consider specifying `platform: linux/amd64` in `docker-compose.yml`.

---

## Project Structure

```
VeriShield-AI-Financial-Verification-Platform/
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI app w/ CRUD endpoints
│   │   ├── models.py       # SQLAlchemy models (User, Business)
│   │   ├── database.py     # Postgres + Neo4j config
│   │   ├── crud.py         # Encapsulated DB logic
│   │   ├── schemas.py      # Pydantic schemas for request/response
│   │   └── __init__.py
│   ├── tests/
│   │   └── test_main.py    # Integration tests
│   ├── scripts/
│   │   └── seed_data.py    # Faker-based data seeding script
│   ├── Dockerfile
│   ├── requirements.txt
│   └── __init__.py
├── docker-compose.yml
├── .gitignore
├── .dockerignore
├── LICENSE
└── README.md
```

---

## Roadmap

1. **Phase 2**: (Done) CRUD endpoints, secure password handling, tests, seeding script.  
2. **Phase 3**: Event-driven architecture with **Kafka** for asynchronous verification workflows.  
3. **Phase 4**: **Machine Learning** integration for risk scoring.  
4. **Phase 5**: Advanced **Neo4j** usage for graph-based fraud detection.  
5. **Phase 6**: Cloud deployment (AWS) with scaling and CI/CD pipelines.  
6. **Phase 7**: Observability (metrics, logs, alerts) and performance tuning.

---

## License

This project is available under the **[MIT License](LICENSE)**. Feel free to use, modify, and distribute under the license terms.

---

## Contact

For questions, feature requests, or contributions:

- **Maintainer**: [harshilbhandari01@gmail.com](mailto:harshilbhandari01@gmail.com)

We welcome **feedback** and **pull requests** to drive innovation in financial identity verification, fraud detection, and risk assessment. **Happy building!**