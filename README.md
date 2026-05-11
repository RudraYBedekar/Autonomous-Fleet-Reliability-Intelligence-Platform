# ⚠️ Important Notice

**Do not push this project to a public GitHub repository.**

This project contains files (such as `.env`, local data, and credentials) that are protected by `.gitignore` but may still contain sensitive or private information. Always review your files and repository settings before sharing or publishing.


# Autonomous Fleet Reliability Intelligence Platform 🚜

## Project Purpose

This project was created as a hands-on learning platform to explore modern, real-time data engineering, analytics, and AI techniques in the context of autonomous vehicle fleet management. It is designed for anyone interested in building scalable, cloud-ready systems and understanding how streaming, analytics, and AI can be combined for actionable insights. The platform is ideal for:
- Learning distributed systems and event-driven architectures
- Experimenting with real-time analytics and anomaly detection
- Practicing full-stack development with modern tools
- Demonstrating end-to-end solutions for reliability and observability

---

## 🏗️ System Architecture

- **Frontend**: React, Tailwind CSS, Vite, Deck.gl (high-performance map rendering)
- **Backend API**: FastAPI, WebSockets
- **Streaming Layer**: Apache Kafka (KRaft mode)
- **Database**: PostgreSQL (or SQLite for local testing) via SQLAlchemy
- **ML & Analytics**: Isolation Forest, Z-Score Anomaly Detection, RUL Forecasting
- **AI Copilot**: LangChain + OpenAI RAG for root cause analysis

## 🚀 Getting Started (No Docker Required)

This project is designed to run locally on Windows using Python virtual environments and native Kafka binaries.

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)

### Quick Start
1. **Setup backend and Kafka:**
	```cmd
	cd infrastructure
	setup.bat
	```
2. **Install frontend dependencies:**
	```cmd
	cd ../frontend
	npm install
	cd ..
	```
3. **Start all services:**
	```cmd
	cd infrastructure
	start.bat
	```

### Access Points
- **Dashboard:** [http://localhost:5173](http://localhost:5173)
- **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
*(If on Linux/Mac, you'll need to install Kafka and run it manually, or adapt the shell commands)*


### Configuration
A `.env` file will be created in the root directory on first run:
- Keep `DATABASE_URL` as SQLite for quick start, or set to PostgreSQL for production.
- Add your `OPENAI_API_KEY` to enable the AI Copilot feature.

### Access Points
- **Dashboard**: [http://localhost:5173](http://localhost:5173)
- **API Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)


## ✨ Key Features
- **Live WebSocket Streaming:** Real-time vehicle movement and chart updates
- **Root Cause Analysis Engine:** AI and heuristics distinguish between sensor anomalies (e.g., "Cooling Fan Failure" vs. "Power Fluctuation")
- **AI Fleet Copilot:** Ask questions like "Which vehicles are failing?" directly in the UI
- **Predictive Maintenance:** Forecast remaining useful life (RUL) for components
- **Modern, Modular Codebase:** Easily extend or adapt for new use cases

---

## 📸 Screenshots

Below are sample screenshots of the dashboard and analytics views you can expect from this project:

### Dashboard Overview
![Dashboard Overview](assets/dashboard_overview.png)

### Geospatial Fleet View
![Geospatial View](assets/geospatial_view.png)

### Predictive Maintenance Analytics
![Predictive Maintenance](assets/predictive_maintenance.png)

---

## License
This project is for educational and demonstration purposes. Feel free to use, modify, and extend it for your own learning or prototyping needs.

