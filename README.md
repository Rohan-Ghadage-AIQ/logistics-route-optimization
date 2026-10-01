# Logistics Route Optimization System

> **Production-grade fleet route optimization system** powered by **Valhalla** (road-network routing engine) and **Google OR-Tools** (constraint-based operations research solver).

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![Valhalla](https://img.shields.io/badge/Valhalla-3.4-orange)
![OR-Tools](https://img.shields.io/badge/OR--Tools-9.11-red?logo=google)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![Leaflet](https://img.shields.io/badge/Leaflet-1.9-brightgreen?logo=leaflet)

---

## Table of Contents

- [Overview](#overview)
- [How Route Optimization Works: Valhalla vs Google OR-Tools](#how-route-optimization-works-valhalla-vs-google-or-tools)
- [Mathematical Formulation (Basics to Advanced)](#mathematical-formulation-basics-to-advanced)
- [System Architecture & Pipeline](#system-architecture--pipeline)
- [Project Directory Structure](#project-directory-structure)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [UI & Theme System](#ui--theme-system)

---

## Overview

The **Logistics Route Optimization System** allows logistics managers to:
1. **Upload** delivery manifests (Excel/CSV) containing delivery addresses, parcel weights, and customer time windows.
2. **Geocode** addresses to high-precision geographic coordinates with automatic caching.
3. **Compute Real Road Networks** using Valhalla's OpenStreetMap distance and duration matrix (`/sources_to_targets`).
4. **Optimize Multi-Vehicle Fleet Routes** using Google OR-Tools CVRPTW solver, enforcing vehicle capacity limits, driver shifts (e.g. 07:00–09:00, 09:00–18:00, 18:00–21:00), and eliminating idle waiting time.
5. **Generate Turn-by-Turn Maneuvers & Polylines** using Valhalla's `/route` engine.
6. **Inspect & Manage Schedules** via an interactive, human-designed Yellow/Black/Grey Leaflet dashboard.
7. **Export Schedules** as downloadable Excel manifests with complete ETAs and stop sequences.

---

## How Route Optimization Works: Valhalla vs Google OR-Tools

A common question in logistics system design: **Can Valhalla optimize routes directly?**

### 1. What Valhalla Does
Valhalla provides an `/optimized_route` endpoint. However, Valhalla's native optimizer is a **single-vehicle Travelling Salesperson Problem (TSP)** heuristic (2-opt). It is designed to reorder waypoints for a single vehicle without constraints.

### 2. Why Real Fleet Logistics Requires Google OR-Tools
Real-world delivery operations face the **Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)**:
- Multiple heterogeneous vehicles with maximum payload limits (e.g. 500 kg per van).
- Specific driver working shifts (Vehicles 1–3: 07:00–09:00, Vehicles 4–6: 09:00–18:00, Vehicles 7–10: 18:00–21:00).
- Customer time windows (e.g., Deliver strictly between 10:00 and 13:00).
- Minimization of idle driver waiting time and route span.
- Penalties for unassigned orders.

### 3. The Two-Engine Architecture
Our system pairs both engines in their ideal roles:
1. **Valhalla** acts as the **Road Network Topology Engine**: It computes the true road-distance and driving-duration matrix ($N \times N$) and generates high-resolution road polylines with turn-by-turn maneuvers.
2. **Google OR-Tools** acts as the **Operations Research Optimization Engine**: It takes Valhalla's matrix and solves the multi-vehicle CVRPTW integer program using Guided Local Search.

---

## Mathematical Formulation (Basics to Advanced)

### 1. Distance Metrics

#### Haversine Geodesic Metric (Spatial Reference)
For coordinates $(\phi_1, \lambda_1)$ and $(\phi_2, \lambda_2)$ in radians with Earth radius $R = 6371\text{ km}$:

$$\Delta \phi = \phi_2 - \phi_1, \quad \Delta \lambda = \lambda_2 - \lambda_1$$

$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)$$

$$d_{\text{haversine}}(i, j) = 2 R \arcsin\left(\sqrt{a}\right)$$

#### Real Road Network Graph Metric (Valhalla)
For directed road network graph $G = (V_{\text{road}}, E_{\text{road}})$, where $\mathcal{P}_{ij}^{*}$ is the optimal shortest/fastest road path from node $i$ to node $j$:

$$d_{ij} = \sum_{e \in \mathcal{P}_{ij}^{*}} \text{length}(e)$$

$$\tau_{ij} = \sum_{e \in \mathcal{P}_{ij}^{*}} \frac{\text{length}(e)}{v(e, \text{traffic})}$$

---

### 2. CVRPTW Mixed-Integer Linear Program

#### Sets & Indices
- $K = \{1, \dots, m\}$: Set of delivery vehicles.
- $C = \{1, \dots, n\}$: Set of delivery stops / orders.
- $V = \{0\} \cup C$: Node set where $0$ is the Central Logistics Hub.

#### Parameters
- $Q_k$: Payload capacity of vehicle $k$ (kg).
- $q_i$: Weight of order $i$ ($q_0 = 0$).
- $[e_i, l_i]$: Delivery time window for order $i$ (minutes from midnight).
- $s_i$: Service/unloading duration at stop $i$.
- $[\text{ShiftStart}_k, \text{ShiftEnd}_k]$: Operational shift of vehicle $k$.
- $F_k, c_k$: Fixed vehicle dispatch cost and cost per km.
- $P_i$: Penalty cost for dropping order $i$.
- $\beta$: Vehicle shift span penalty coefficient.

#### Decision Variables
- $x_{ijk} \in \{0, 1\}$: Binary variable indicating vehicle $k$ drives directly from node $i$ to node $j$.
- $t_{ik} \ge 0$: Arrival timestamp of vehicle $k$ at node $i$.
- $u_{ik} \ge 0$: Cumulative load of vehicle $k$ after visiting node $i$.
- $y_i \in \{0, 1\}$: 1 if order $i$ is assigned; 0 if dropped.

#### Objective Function
$$\min Z = \sum_{k \in K} F_k \sum_{j \in C} x_{0jk} + \sum_{k \in K} c_k \sum_{i \in V} \sum_{j \in V} d_{ij} x_{ijk} + \beta \sum_{k \in K} \left( t_{\text{end}, k} - t_{\text{start}, k} \right) + \sum_{i \in C} P_i (1 - y_i)$$

#### Constraints
1. **Degree & Flow Conservation:**
   $$\sum_{k \in K} \sum_{j \in V, j \neq i} x_{ijk} = y_i \quad \forall i \in C$$
   $$\sum_{j \in V, j \neq i} x_{ijk} - \sum_{j \in V, j \neq i} x_{jik} = 0 \quad \forall i \in C, \forall k \in K$$
   $$\sum_{j \in C} x_{0jk} \le 1, \quad \sum_{i \in C} x_{i0k} = \sum_{j \in C} x_{0jk} \quad \forall k \in K$$

2. **Capacity Conservation:**
   $$u_{ik} + q_j - M(1 - x_{ijk}) \le u_{jk} \quad \forall i, j \in V, \forall k \in K$$
   $$q_i \le u_{ik} \le Q_k \quad \forall i \in C, \forall k \in K$$

3. **Time Progression & Driver Shift Bounds:**
   $$t_{ik} + s_i + \tau_{ij} - M(1 - x_{ijk}) \le t_{jk} \quad \forall i, j \in V, \forall k \in K$$
   $$e_i \le t_{ik} \le l_i \quad \forall i \in C, \forall k \in K$$
   $$\text{ShiftStart}_k \le t_{0k}^{\text{depart}} \le t_{0k}^{\text{return}} \le \text{ShiftEnd}_k \quad \forall k \in K$$

4. **Strict Conservation Identity:**
   $$\text{Total Duration}_k \equiv \sum_{\text{legs}} \tau_{\text{driving}} + \sum_{\text{stops}} \tau_{\text{service}} + \sum_{\text{stops}} \tau_{\text{waiting}}$$

---

## System Architecture & Pipeline

```
[ Excel / CSV Manifest ]
           │
           ▼
[ Stage 1: Validation ] ──► Schema, weight & time window verification
           │
           ▼
[ Stage 2: Geocoding ]  ──► Nominatim Geocoder + Persistent Cache + Hub Cluster
           │
           ▼
[ Stage 3: Matrix Gen ] ──► Valhalla /sources_to_targets (NxN Road Matrix)
           │
           ▼
[ Stage 4: OR-Tools ]   ──► CVRPTW Solver (Capacity, Shifts, Span Minimization)
           │
           ▼
[ Stage 5: Routes ]     ──► Valhalla /route (Road Polylines & Maneuvers)
           │
           ▼
[ Interactive UI ]      ──► React 19 + Leaflet Dashboard + Excel Export
```

---

## Project Directory Structure

```
logistics-route-optimization/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST endpoints (jobs, fleet, export)
│   │   ├── core/            # Config and environment settings
│   │   ├── database/        # SQLite models, sessions & fleet seed
│   │   ├── models/          # Pydantic schemas
│   │   ├── services/
│   │   │   ├── geocoding/   # Nominatim geocoder & persistent cache
│   │   │   ├── matrix/      # Valhalla distance/duration matrix client
│   │   │   ├── optimization/# Google OR-Tools CVRPTW solver
│   │   │   ├── pipeline.py  # End-to-end pipeline orchestrator
│   │   │   └── route_builder.py # Canonical route & geometry builder
│   │   └── main.py          # FastAPI application entrypoint
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # UI Components (Navbar, SummaryStats, RouteMap, etc.)
│   │   ├── hooks/           # Polling & fleet hooks
│   │   ├── services/        # Axios API client
│   │   ├── types/           # TypeScript interfaces
│   │   ├── App.tsx          # Main workspace
│   │   └── index.css        # Tailwind & Leaflet styling
│   ├── package.json
│   └── vite.config.ts
├── ARCHITECTURE.md          # Detailed mathematical & technical architecture
├── README.md                # Project documentation
└── .gitignore               # Production gitignore
```

---

## Setup & Installation

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & `npm`
- **Valhalla Routing Engine** (Running locally on port 8002 or via Docker)

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Frontend Setup
```bash
cd frontend
npm install
```

---

## Running the Application

### 1. Start Backend Server
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Start Frontend Dashboard
```bash
cd frontend
npm run dev
```
Frontend UI: [http://localhost:5173](http://localhost:5173)

---

## UI & Theme System

The user interface follows a modern, human-crafted **Yellow, Black, and Grey** industrial logistics theme:
- **Amber / Yellow (`#f59e0b` / `#fbbf24`):** Primary branding, CTA buttons, active route highlights.
- **Charcoal / Black (`#0f172a` / `#1e293b`):** Top navigation, high-contrast headings.
- **Slate Grey (`#f8fafc` / `#e2e8f0` / `#64748b`):** Clean card surfaces, borders, and metric chips.