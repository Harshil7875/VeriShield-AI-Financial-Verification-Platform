# **VeriShield** 🛡️ 

<div align="center">

![VeriShield Banner](https://img.shields.io/badge/VeriShield-AI--Powered%20Financial%20Identity%20Verification-blue?style=for-the-badge)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg)](https://www.postgresql.org/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5-008CC1.svg)](https://neo4j.com/)
[![Kafka](https://img.shields.io/badge/Kafka-3-231F20.svg)](https://kafka.apache.org/)
[![Machine Learning](https://img.shields.io/badge/ML-Enabled-FF6F00.svg)](#features-phase-4)
[![Status](https://img.shields.io/badge/Status-Active%20Development-green)](https://github.com/Harshil7875/VeriShield-AI-Financial-Verification-Platform)

*An open-source, modular, and scalable backend solution for KYC/KYB processes with advanced fraud detection*

</div>

## 🔍 **Overview**

VeriShield is an **open-source initiative** to build a **modular**, **scalable**, and **efficient** backend solution for **KYC (Know Your Customer)** and **KYB (Know Your Business)** processes. By leveraging technologies such as **FastAPI**, **PostgreSQL**, **Neo4j**, **Kafka**, and **Machine Learning**, VeriShield automates identity verification, detects fraud, and delivers real-time risk scoring. Its **community-driven** architecture ensures flexibility and extensibility, allowing developers to integrate additional data sources (like IP watchlists or advanced device intelligence) and sophisticated ML workflows.

<p align="center">
  <a href="#introduction">Introduction</a> •
  <a href="#project-goals">Goals</a> •
  <a href="#features-phase-1">Features</a> •
  <a href="#quick-start-docker-only">Quick Start</a> •
  <a href="#project-structure">Structure</a> •
  <a href="#roadmap">Roadmap</a>
</p>

---

## **Table of Contents**

1. [Introduction](#introduction)  
2. [Project Goals](#project-goals)  
   - [Core Objectives](#core-objectives)  
   - [Targeted Real-World Applications](#targeted-real-world-applications)  
3. [Features (Phase 1)](#features-phase-1)  
4. [Features (Phase 2)](#features-phase-2)  
5. [Features (Phase 3)](#features-phase-3)  
6. [Features (Phase 4)](#features-phase-4)  
7. [Quick Start (Docker-Only)](#quick-start-docker-only)  
8. [Testing (Docker-Only)](#testing-docker-only)  
9. [Seeding Data (Optional)](#seeding-data-optional)  
10. [Requirements](#requirements)  
11. [Project Structure](#project-structure)  
12. [Roadmap](#roadmap)  
13. [License](#license)  
14. [Contact](#contact)

---

## **Introduction** 📋

VeriShield serves as a **backend simulation** for financial institutions, fintech startups, and e-commerce platforms requiring **KYC/KYB** capabilities. By automating identity verification, fraud detection, and real-time risk assessments, it addresses complex regulatory requirements in identity management. Key highlights:

- **Automated identity verification** reduces human error and manual overhead.  
- **Fraud detection** employing classical ML, deep learning, or **graph neural networks (GNN)**—especially relevant for ring-based or multi-owner collusion.  
- **Real-time risk scoring** integrated with **Kafka**.  
- **Graph-based analysis** (Neo4j) for discovering hidden suspicious relationships (e.g., shared IP usage, ring leaders, multi-owner webs).

By design, **VeriShield** is **modular**—enabling quick enhancements (like IP watchlists or synergy-based labeling) to keep pace with evolving fraud tactics.

---

## **Project Goals** 🎯

### **Core Objectives**

1. **Automate KYC/KYB** processes, reducing manual checks while maintaining regulatory compliance.  
2. **Detect anomalies & potential fraud** using synergy-based labeling, ring expansions, and watchlist IP logic.  
3. **Model entity relationships** in a **graph database** for advanced ring or multi-owner detection (Neo4j).  
4. **Harness asynchronous workflows** using **Kafka**, ensuring robust & scalable verification at high volumes.  
5. **Enable easy extensibility** through microservices, containerization, and a plug-in approach for advanced ML or GNN solutions.

### **Targeted Real-World Applications**

- **Fintech** (AML, user signups, suspicious IP tracking)  
- **Digital Banking & E-Commerce** (fraud detection, real-time risk-based transaction blocking)  
- **Analytics & Risk**: Combining ML & GNN for advanced ring-based anomaly detection in complex user–business–IP graphs.

---

## **Features (Phase 1)** 🏗️

1. **Dockerized Setup**: Local deployment with **FastAPI**, **PostgreSQL**, **Neo4j**.  
2. **Basic Endpoint**: A `/health` route verifying the service's operational status.  
3. **Initial Testing**: Basic Pytest coverage verifying environment and container synergy.  
4. **Foundational Structure**: Clear environment variables, Docker configuration, and code organization.

---

## **Features (Phase 2)** 🔧

1. **CRUD Endpoints** (FastAPI):  
   - **User** & **Business** create/read/update.  
   - Basic data validation with Pydantic.  
2. **Database Integration**:  
   - **SQLAlchemy** + Postgres for standard relational data.  
   - **Neo4j** driver for future graph-based queries or ring expansions.  
3. **Secure Passwords**:  
   - **bcrypt** hashing.  
   - Potential to expand for more advanced authentication flows.  
4. **Advanced Testing**:  
   - Integration tests checking CRUD correctness (e.g., duplicates, 404s).  
   - Additional Docker-based tests.

---

## **Features (Phase 3)** ⚡

1. **Event-Driven Architecture** via **Kafka**:  
   - **Producer** publishes events (`user_created`, `user_verified`).  
   - **Consumer** listens and sets `is_verified=true` in the background.  
2. **Retries & DLQ**:  
   - Automatic re-delivery on partial failures.  
   - "Dead Letter Queue" for unresolvable messages.  
3. **Scaling**:  
   - As user volume increases, scale consumer services horizontally.  
4. **Test Coverage**:  
   - Integration tests verifying event-driven flows.  
   - Demonstrates asynchronous identity checks.

---

## **Features (Phase 4)** 🧠

### **Machine Learning Integration & Advanced Fraud Detection**

1. **Risk Scoring Service**  
   - ML pipeline generating risk scores for new signups or business registrations.  
   - Could run offline in batch or real-time in Kafka consumer.

2. **`verishield_ml_experiments` Sub-Project**  
   - Found in **`verishield_ml_experiments/`**.  
   - **Synthetic data** creation (multi-pass synergy, ring leaders, IP collisions).  
   - **EDA & Model Training** notebooks (XGBoost, Keras MLP, **GNN**).  
   - Demonstrates **multi-task** classification: user, business, plus **IP** nodes.

3. **Offline + Online Flow**  
   - Offline: train/tune ML or GNN on synthetic or partial real data.  
   - Online: integrate best models into the microservice or consumer for real-time risk flags.

4. **Neo4j + GNN**  
   - Phase 5 focuses on deeper integration with Neo4j for ring-based or IP-based subgraphs.  
   - Evaluate suspicious patterns (shared IP usage, colluding ring leaders) to refine fraud detection.

---

## **Quick Start (Docker-Only)** 🚀

1. **Clone**:
   ```bash
   git clone https://github.com/Harshil7875/VeriShield-AI-Financial-Verification-Platform.git
   cd VeriShield-AI-Financial-Verification-Platform
   ```
2. **Launch**:
   ```bash
   docker compose up -d --build
   ```
   - Runs backend (FastAPI), consumer, Postgres, Neo4j, Kafka, Zookeeper.  
3. **Check**:
   ```bash
   docker compose ps
   ```
   - Ensure containers are healthy.  
4. **Health**:
   - Visit [http://localhost:8000/health](http://localhost:8000/health). Expect `{"status":"OK"}`.  
5. **Logs**:
   - `docker compose logs backend -f`
   - `docker compose logs consumer -f`
6. **Create a User**:
   ```bash
   curl -X POST -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"pass123"}' \
        http://localhost:8000/users
   ```

---

## **Testing (Docker-Only)** 🧪

1. **Enter Container**:
   ```bash
   docker compose exec backend /bin/bash
   ```
2. **Pytest**:
   ```bash
   pytest --cov=app --cov-report=term-missing
   ```
   - Shows coverage and any warnings.

---

## **Seeding Data (Optional)** 📊

1. **Inside** container:
   ```bash
   docker compose exec backend /bin/bash
   ```
2. **Run**:
   ```bash
   cd scripts
   python seed_data.py 10 15 True
   ```
   - Seeds 10 users, 15 businesses, optionally Neo4j data.

---

## **Requirements** 📋

- **Docker** (Docker Desktop or engine + compose)  
- **Git**  
- *(Optional)* Python 3.11+ for local dev  
- *(Optional)* Conda/virtualenv for local environment

> **Apple Silicon**: Our images (e.g. `postgres:15`, `neo4j:5`) support `arm64`. If issues, specify `platform: linux/amd64` in `docker-compose.yml`.

---

## **Project Structure** 📂

```
VeriShield-AI-Financial-Verification-Platform/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI endpoints
│   │   ├── kafka_consumer.py  # Listens for user_created events
│   │   ├── kafka_producer.py  # Publishes user_created events
│   │   ├── models.py          # SQLAlchemy models (User/Business)
│   │   ├── database.py        # Postgres + Neo4j config
│   │   ├── crud.py            # DB logic
│   │   ├── schemas.py         # Pydantic schemas
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_kafka.py
│   │   └── test_main.py
│   ├── scripts/
│   │   └── seed_data.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── __init__.py
├── verishield_ml_experiments/
│   ├── data_generators/
│   ├── notebooks/
│   ├── requirements.txt
│   └── README.md
├── docker-compose.yml
├── LICENSE
└── README.md
```

---

## **Roadmap** 🗺️

1. **Phase 3**: ✅ Kafka-based asynchronous user verification  
2. **Phase 4**: 🔄 ML & GNN integration for advanced risk scoring (ongoing)  
3. **Phase 5**: 📅 Neo4j expansions (graph-based synergy, ring-based analytics)  
4. **Phase 6**: 📅 Cloud deployment, CI/CD  
5. **Phase 7**: 📅 Observability (monitoring, logging, alerting), performance

---

## **License** ⚖️

Licensed under the **[MIT License](LICENSE)**. Feel free to use, modify, and distribute under these terms. We welcome **community contributions** to enhance synergy-based ring detection, IP classification, or advanced GNN integrations.

---

## **Contact** 📬

For questions, feature requests, or contributions:

- **Maintainer**: [harshilbhandari01@gmail.com](mailto:harshilbhandari01@gmail.com)

I appreciate **feedback** and **pull requests** to strengthen identity verification workflows, ring-based detection, multi-task classification, or advanced GNN modeling for real-time fraud prevention.

---

<div align="center">

### Tags

`#KYC` `#KYB` `#FinTech` `#IdentityVerification` `#MachineLearning` `#GraphDatabases` `#FraudDetection` `#OpenSource` `#Neo4j` `#Kafka` `#FastAPI` `#PostgreSQL` `#AML` `#GNN` `#RiskScoring` `#Python` `#Docker` `#AsyncProcessing` `#DataEngineering` `#SecurityCompliance`

</div>
