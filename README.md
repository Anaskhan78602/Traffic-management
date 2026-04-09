# ◈ VTCPS — Virtual Traffic Congestion Prevention System

> An intelligent traffic signal control system using Q-Learning reinforcement learning, SUMO traffic simulation, and a real-time React dashboard.

![Python](https://img.shields.io/badge/Python-3.10+-3d8bff?style=flat-square&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-00e5a0?style=flat-square&logo=react&logoColor=white)
![SUMO](https://img.shields.io/badge/SUMO-1.18-ffb830?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-a78bfa?style=flat-square&logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-ff4757?style=flat-square)

---

## 📌 Overview

VTCPS is a final-year B.Tech project that simulates and optimizes urban traffic signal control using **Reinforcement Learning**. The system trains a Q-Learning agent to minimize vehicle wait times at intersections, compared against a fixed-timer baseline. All simulation data streams live to a command-center style dashboard.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│         (Live Dashboard + Mode Switching)            │
└────────────────────┬────────────────────────────────┘
                     │ HTTP polling (1.5s)
┌────────────────────▼────────────────────────────────┐
│              FastAPI Backend                         │
│         /metrics  /start-simulation                  │
└────────┬───────────────────────┬────────────────────┘
         │                       │
┌────────▼────────┐   ┌──────────▼──────────┐
│  Q-Learning     │   │   SUMO Simulator     │
│  Agent          │   │   via TraCI          │
│  (q_table.pkl)  │   │   (Eclipse SUMO)     │
└─────────────────┘   └─────────────────────┘
```

---

## ✨ Features

- **3 Simulation Modes**
  - `MOCK` — Synthetic traffic, no SUMO required
  - `SUMO` — Full SUMO simulation via TraCI connection
  - `AI` — Q-Learning agent trains live, adapts signal timing in real-time

- **Live Dashboard**
  - Real-time queue heatmaps (N/S/E/W)
  - Sparkline charts for wait time & throughput
  - Radial gauges for ε (epsilon), avg wait, Q-table size
  - Episode reward history bar chart
  - Mode-aware animated transitions

- **Q-Learning Agent**
  - State: discretized queue lengths per direction
  - Actions: switch signal phase (NS / EW)
  - Reward: negative total wait time
  - Epsilon-greedy exploration with decay
  - Trained model saved to `models/trained_q_table.pkl`

---

## 🗂️ Project Structure

```
VTCPS/
├── backend/
│   ├── main.py                  # FastAPI app, /metrics, /start-simulation
│   ├── simulator/
│   │   ├── mock_sim.py          # Synthetic traffic simulator
│   │   ├── sumo_sim.py          # SUMO + TraCI simulator
│   │   └── ai_sim.py            # Q-Learning training loop
│   ├── agent/
│   │   └── q_agent.py           # Q-Learning agent class
│   └── models/
│       └── trained_q_table.pkl  # Saved Q-table (after training)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main dashboard component
│   │   ├── App.css              # Full dashboard styling
│   │   └── Services/
│   │       └── api.js           # Axios API calls
│   └── package.json
│
├── sumo_config/                 # SUMO network & route files
│   ├── network.net.xml
│   └── routes.rou.xml
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Eclipse SUMO](https://sumo.dlr.de/docs/Downloads.php) (for SUMO mode)

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/VTCPS.git
cd VTCPS
```

### 2. Backend setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Open dashboard

```
http://localhost:5173
```

---

## 🚀 Usage

1. Start the backend server
2. Start the frontend dev server
3. Open the dashboard in your browser
4. Click **MOCK**, **SUMO**, or **AI** to start a simulation
5. Watch metrics update live every 1.5 seconds

> For SUMO mode: ensure Eclipse SUMO is installed and `SUMO_HOME` environment variable is set.

---

## 📊 Results

| Mode | Avg Wait Time | Improvement |
|------|--------------|-------------|
| Fixed Timer (baseline) | ~28s | — |
| Mock AI Agent | ~18s | ~36% |
| SUMO + Q-Learning | ~15s | ~46% |

---

## 🧠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, CSS3 |
| Backend | FastAPI, Python 3.10 |
| Simulation | Eclipse SUMO 1.18 |
| RL Agent | Q-Learning (custom) |
| TraCI | Python TraCI API |
| Data | Pickle (Q-table persistence) |

---

## 👥 Team

| Name | Role |
|------|------|
| Anas Khan | RL Agent, Backend, Dashboard |
| [Member 2] | SUMO Network Configuration |
| [Member 3] | Frontend & Visualization |
| [Member 4] | Data Analysis & Report |

---

## 📄 License

MIT License — free to use for academic purposes.

---

> B.Tech Final Year Project — 2025 | Department of Computer Science
