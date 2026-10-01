# Architecture & Mathematical Formulation — Logistics Route Optimization System

**Version:** 2.1.0  
**Author:** AIQ Space Ventures Private Limited  
**Platform:** FastAPI + Valhalla + Google OR-Tools + React 19 + Leaflet  

---

## 1. Mathematical Foundations & Formulations (Basics to Advanced)

The routing engine solves the **Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)** with heterogeneous fleet capacity, driver shift bounds, waiting time minimization, and drop penalties.

### 1.1 Distance & Metric Foundations

#### A. Geodesic Metric (Haversine Formula — Used for Spatial Clustering & Validation)
For two coordinates $(\phi_1, \lambda_1)$ and $(\phi_2, \lambda_2)$ in radians with Earth radius $R = 6371.0\text{ km}$:

$$\Delta \phi = \phi_2 - \phi_1, \quad \Delta \lambda = \lambda_2 - \lambda_1$$

$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)$$

$$d_{\text{haversine}}(i, j) = 2 R \cdot \arcsin\left(\sqrt{a}\right)$$

#### B. Road Network Metric (Valhalla OpenStreetMap Topology Graph)
Real road travel does not follow straight lines. The distance $d_{ij}$ and driving duration $\tau_{ij}$ are evaluated over directed road network graph $G = (V_{\text{road}}, E_{\text{road}})$ using dynamic costing models:

$$d_{ij} = \sum_{e \in \mathcal{P}_{ij}^{*}} \text{length}(e)$$

$$\tau_{ij} = \sum_{e \in \mathcal{P}_{ij}^{*}} \frac{\text{length}(e)}{v(e, \text{traffic})}$$

where $\mathcal{P}_{ij}^{*}$ is the time-optimal path calculated by Valhalla's bidirectional A* algorithm.

---

### 1.2 Mathematical Optimization Model (CVRPTW)

#### Sets and Indices
- $K = \{1, 2, \dots, m\}$: Set of available fleet delivery vehicles.
- $C = \{1, 2, \dots, n\}$: Set of customer delivery orders (parcels).
- $V = \{0\} \cup C$: Complete node set, where node $0$ denotes the **Central Logistics Depot**.

#### Parameters
- $Q_k$: Maximum payload capacity of vehicle $k \in K$ (kg).
- $q_i$: Weight of parcel for order $i \in C$ (with $q_0 = 0$).
- $[e_i, l_i]$: Delivery time window for order $i \in C$ in minutes from midnight ($e_i$ is early arrival bound, $l_i$ is latest arrival bound).
- $s_i$: Unloading / service duration at order $i \in C$ ($s_0 = 0$).
- $[\text{ShiftStart}_k, \text{ShiftEnd}_k]$: Operational working shift for vehicle $k \in K$.
- $d_{ij}$: Road distance from node $i$ to node $j$ (km).
- $\tau_{ij}$: Road travel duration from node $i$ to node $j$ (minutes).
- $F_k$: Fixed vehicle dispatch cost.
- $c_k$: Variable operational cost per kilometer.
- $P_i$: Penalty cost for leaving order $i$ unassigned (dropped order).
- $\beta$: Vehicle span penalty coefficient (minimizes idle waiting and active shift duration).

#### Decision Variables
- $x_{ijk} \in \{0, 1\}$: Binary variable $= 1$ if vehicle $k$ travels directly from node $i$ to node $j$; $0$ otherwise.
- $t_{ik} \ge 0$: Continuous variable representing arrival time of vehicle $k$ at node $i$.
- $u_{ik} \ge 0$: Continuous variable representing cumulative parcel load on vehicle $k$ after visiting node $i$.
- $y_i \in \{0, 1\}$: Binary variable $= 1$ if order $i$ is served; $0$ if dropped.

---

### 1.3 Optimization Objective Function

$$\min Z = \underbrace{\sum_{k \in K} F_k \sum_{j \in C} x_{0jk}}_{\text{Fixed Vehicle Activation Cost}} + \underbrace{\sum_{k \in K} c_k \sum_{i \in V} \sum_{j \in V} d_{ij} x_{ijk}}_{\text{Variable Road Distance Cost}} + \underbrace{\beta \sum_{k \in K} \left( t_{\text{end}, k} - t_{\text{start}, k} \right)}_{\text{Shift Span / Idle Wait Penalty}} + \underbrace{\sum_{i \in C} P_i (1 - y_i)}_{\text{Dropped Order Penalty}}$$

---

### 1.4 Constraints

#### 1. Order Assignment & Flow Conservation
Each order is visited at most once by at most one vehicle:
$$\sum_{k \in K} \sum_{j \in V, j \neq i} x_{ijk} = y_i \quad \forall i \in C$$

Every vehicle departing the Central Depot must return to the Central Depot (Closed Circuit):
$$\sum_{j \in C} x_{0jk} \le 1 \quad \forall k \in K$$
$$\sum_{j \in V, j \neq i} x_{ijk} - \sum_{j \in V, j \neq i} x_{jik} = 0 \quad \forall i \in C, \forall k \in K$$
$$\sum_{i \in C} x_{i0k} = \sum_{j \in C} x_{0jk} \quad \forall k \in K$$

#### 2. Vehicle Capacity Constraints
Cumulative weight tracking along route segments:
$$u_{ik} + q_j - M(1 - x_{ijk}) \le u_{jk} \quad \forall i, j \in V, \forall k \in K$$
$$q_i \le u_{ik} \le Q_k \quad \forall i \in C, \forall k \in K$$
where $M$ is a sufficiently large positive constant.

#### 3. Time Windows, Service, and Waiting Slack
Arrival progression with driving duration and service time:
$$t_{ik} + s_i + \tau_{ij} - M(1 - x_{ijk}) \le t_{jk} \quad \forall i, j \in V, \forall k \in K$$

Customer time-window bounds:
$$e_i \le t_{ik} \le l_i \quad \forall i \in C, \forall k \in K$$

Driver shift boundary constraints:
$$\text{ShiftStart}_k \le t_{0k}^{\text{depart}} \le t_{0k}^{\text{return}} \le \text{ShiftEnd}_k \quad \forall k \in K$$

Waiting time at stop $i$ when vehicle arrives earlier than $e_i$:
$$w_{ik} = \max(0, \, e_i - (t_{\text{prev}, k} + s_{\text{prev}} + \tau_{\text{prev}, i}))$$

#### 4. Strict Conservation Invariant (Single Source of Truth)
Every calculated route strictly obeys the conservation law:
$$\text{Total Duration}_k \equiv \sum_{\text{legs}} \tau_{ij}^{\text{driving}} + \sum_{\text{stops}} s_i^{\text{service}} + \sum_{\text{stops}} w_{ik}^{\text{waiting}}$$
$$t_{0k}^{\text{return}} - t_{0k}^{\text{depart}} \equiv \text{Total Duration}_k$$

---

## 2. Engine Synergy: Valhalla vs Google OR-Tools

### Why Valhalla Alone Cannot Solve Multi-Vehicle Fleet Optimization
Valhalla provides an `/optimized_route` endpoint. However:
1. Valhalla's `/optimized_route` is a **single-vehicle Travelling Salesperson Problem (TSP)** heuristic (2-opt).
2. It cannot allocate 50+ orders among 10 distinct vehicles.
3. It cannot enforce heterogeneous vehicle capacities ($Q_k = 500\text{ kg}$).
4. It cannot schedule across multi-shift driver windows (07:00–09:00, 09:00–18:00, 18:00–21:00).
5. It cannot minimize waiting time slack or handle unassigned order penalties.

### The Production Two-Engine Solution
| Responsibility | Engine | API / Module | Output |
| :--- | :--- | :--- | :--- |
| **Road Network Graph & Matrix** | **Valhalla** | `/sources_to_targets` | Exact $N \times N$ Road Distance & Travel Time Matrix |
| **Combinatorial Fleet Optimization** | **Google OR-Tools** | `RoutingModel` (CVRPTW) | Optimal Stop Sequences, Vehicle Assignments, and Timestamps |
| **Turn-by-Turn Road Geometry** | **Valhalla** | `/route` | High-Resolution Polyline6 Coordinates & Maneuver Instructions |

---

## 3. End-to-End Pipeline Data Flow

```
[ Excel / CSV Manifest ]
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ Stage 1: Validation & Excel Ingestion                  │
│ • Validates required columns, weights, time windows    │
│ • Detects and parses consignment IDs                   │
└────────────────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ Stage 2: Nominatim Geocoding with Spatial Hub Cluster  │
│ • Caches lat/lon pairs in geocode_cache.json           │
│ • Resolves Central Logistics Hub coordinates           │
└────────────────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ Stage 3: Valhalla Matrix Generation                    │
│ • Calls Valhalla /sources_to_targets                   │
│ • Assembles exact NxN road distance & duration arrays  │
└────────────────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ Stage 4: Google OR-Tools CVRPTW Solver                 │
│ • Enforces Vehicle Capacity (kg)                       │
│ • Enforces Driver Working Shifts                       │
│ • Minimizes Route Span & Idle Waiting                  │
│ • Applies Guided Local Search (GLS) Metaheuristics     │
└────────────────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ Stage 5: Canonical Route Builder & Geometry            │
│ • Calls Valhalla /route for turn-by-turn road curves   │
│ • Enforces Driving + Service + Waiting = Total Duration│
│ • Renders interactive routes with yellow/black UI      │
└────────────────────────────────────────────────────────┘
```

---

## 4. Frontend Architecture & Design System

The user interface is built with **React 19, TypeScript, TailwindCSS, and Leaflet**, following a **Yellow, Black, and Grey** industrial palette:

- **Primary Brand / Action Accent:** `#f59e0b` (Amber 500) / `#fbbf24` (Amber 400)
- **Primary Structure / Navbar / Headers:** `#0f172a` (Slate 900) / `#1e293b` (Slate 800)
- **Backgrounds & Workspaces:** `#f8fafc` (Slate 50) / `#ffffff` (Pure White)
- **Borders & Dividers:** `#e2e8f0` (Slate 200) / `#cbd5e1` (Slate 300)
- **Status Badges:** Emerald (`#059669`) for On-Time, Amber (`#d97706`) for Waiting, Rose (`#dc2626`) for Late/Dropped.