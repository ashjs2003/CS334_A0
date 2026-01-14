# Rules Before Roads  
**Simulating How Policy Shapes Urban Opportunity**

This project is an **agent-based urban simulation** that explores how *policy rules*—not just physical infrastructure—shape access, mobility, and wealth outcomes in cities.

Two agents operate in the **same city**, navigating identical street networks and resources.  
What differs are the **rules** governing access, visibility, mobility, and privilege.

Small rule changes lead to **large, emergent inequalities**.

---

## 🎥 Simulation Demo

Below is a recorded run of the simulation showing:
- Two players (A and B)
- Policy-driven access differences
- Resource competition
- Wealth divergence over time

<video src="simulation.avi" controls width="800"></video>

> If the video does not play directly in your browser,  
> [download the video here](simulation.mp4).

---

## 🏙️ What This Simulation Models

- **Urban mobility networks** (OpenStreetMap via OSMnx)
- **Agent-based decision making**
- **Policy constraints** such as:
  - Transit access
  - Resource spawn bias
  - Vision / information radius
  - Access restrictions
- **Emergent wealth accumulation**
- **Narrative-driven scenarios** powered by LLM-generated policy rules

---

## 🧠 Core Idea

> *Cities do not treat everyone equally — rules decide who benefits.*

Instead of changing the city geometry, this simulation changes:
- **Who can move**
- **What they can see**
- **Where opportunities appear**

The result is inequality that **emerges naturally**, without hard-coding outcomes.

---

## 🧩 Key Components

- `Sim` — agent-based simulation engine  
- `FaithSystem` — converts narrative policy descriptions into simulation parameters  
- `run_2d_sim` — real-time 2D visualization with wealth tracking  
- OSMnx + NetworkX — urban network modeling  
- Matplotlib — animated visualization  

---

## 🚀 Use Cases

- Urban planning research
- Policy scenario testing
- Climate / disaster impact storytelling
- Interactive demos
- AI + cities portfolios

---

## 📌 Future Extensions

- Dynamic disasters (flooding, outages)
- Multi-agent scaling
- Policy comparison batch runs
- Automated narrative generation
- Interactive web-based visualization

## Inspirations

Chen, Baoyang, Xian Xu, and Huamin Qu. "Multi Layered Autonomy and AI Ecologies in Robotic Art Installations." Proceedings of the ACM on Computer Graphics and Interactive Techniques 8.3 (2025): 1-9.
