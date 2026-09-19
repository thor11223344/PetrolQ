# 🎥 PetrolQ — Prototype Demo Video Guide & Script

This document contains step-by-step recording scripts and actions for recording your hackathon/project evaluation demo video.

---

# ⚡ Option A: 60–90 Second Lightning Demo (Recommended for Fast Judging)

### ⏱️ Timeline Overview
* **0:00 – 0:15 (15s):** The Problem & Core Solution
* **0:15 – 0:35 (20s):** Geospatial Offset Radar & Wellhead Provenance
* **0:35 – 0:55 (20s):** Anti-Fabrication AI Document Ingestion (RAG)
* **0:55 – 1:20 (25s):** Live Telemetry Simulation & Threat Injection
* **1:20 – 1:30 (10s):** Closing Impact

---

## 🎬 Second-by-Second Walkthrough

### 1. The Hook (0:00 – 0:15)
* **On Screen:** Full dashboard view in full screen (`F11`).
* **Mouse Action:** Cursor hovers over active well and Look-Ahead Radar.
* **Voiceover:**
  > *"Unforeseen downhole hazards like gas kicks and stuck pipe cost oil operators millions in Non-Productive Time and risk catastrophic blowouts. **PetrolQ** turns unstructured historical drilling reports into a real-time, predictive look-ahead radar for active drilling operations."*

---

### 2. Geospatial Offset Radar & Provenance (0:15 – 0:35)
* **On Screen:** Interactive Map (`WellMap`).
* **Mouse Actions:**
  1. Slide the **Search Radius Slider** (smoothly expands from 30km to 60km without screen jitter).
  2. Click on an offset well marker.
  3. Click open the **"Provenance & Geological Data" accordion/dropdown** to show operator, depth, casing, and formation tops.
* **Voiceover:**
  > *"Our geospatial engine maps regional basins and lets engineers dynamically adjust offset search radiuses. Clicking any well reveals its full geological provenance, casing program, and formation tops—eliminating opaque black-box data."*

---

### 3. Anti-Fabrication AI Ingestion (0:35 – 0:55)
* **On Screen:** Ingestion / Knowledge Search modal.
* **Mouse Actions:**
  1. Show an uploaded DDR / End-of-Well PDF.
  2. Point to the extracted incident table: **Event Type, Depth, Casing/Cement data**, and the **verifiable Source Text Snippet**.
* **Voiceover:**
  > *"Our OCR and hybrid RAG pipeline ingests complex Daily Drilling Reports. It extracts not only kicks and fluid loss events, but also casing and cementing integrity with exact page citations—guaranteeing zero hallucinations."*

---

### 4. Live Telemetry & Hazard Injection (0:55 – 1:20)
* **On Screen:** Bottom Telemetry Control Console.
* **Mouse Actions:**
  1. Click **Play Simulator** (watch live TVD, ROP, and SPP gauges stream).
  2. Click **Gas Kick** (or a **Field Incident** shortcut like `🔥 Kick (3105m)`).
  3. Show the instant warning banner and recommended SOP mitigation (Driller's method, BOP shut-in).
* **Voiceover:**
  > *"In real time, our WITSML telemetry simulator streams live sensor data. If an influx occurs—like this Gas Kick—our system detects the pit gain, correlates it with offset memory, and prescribes instantaneous emergency SOP mitigations before a blowout can develop."*

---

### 5. Closing (1:20 – 1:30)
* **On Screen:** Zoom back out to the full tactical dashboard.
* **Voiceover:**
  > *"PetrolQ combines deep geological memory with real-time rig telemetry to deliver zero surprises downhole. Thank you!"*

---

# 📋 Option B: 3–4 Minute Comprehensive Demo (For Detailed Technical Reviews)

| Time | Section | Focus |
|---|---|---|
| **0:00 - 0:35** | **1. The Hook & Problem** | Upstream drilling risks, NPT costs, unmined PDF knowledge |
| **0:35 - 1:20** | **2. Geospatial Offset Intelligence** | Basin selector, dynamic radius filter, well provenance dropdown |
| **1:20 - 2:10** | **3. AI Document Ingestion (RAG)** | Automated DDR parsing, Casing/Cementing, Zero-fabrication citations |
| **2:10 - 3:00** | **4. Look-Ahead Radar & Hazard Matching** | Proactive depth-based warnings from offset wells, calibrated match % |
| **3:00 - 3:45** | **5. Live Telemetry Simulator & Injection** | Real-time sensor spikes (Gas Kick / Lost Circ / Stuck Pipe) |
| **3:45 - 4:00** | **6. Architecture & Conclusion** | FastAPI, pgvector, hybrid BM25 search, Mapbox GIS |

---

# 💡 Recording Checklist & Best Practices
1. **Screen Setup:**
   - Use browser full-screen mode (**F11** in Chrome / Edge) to hide bookmarks, tabs, and taskbar.
   - Recommended resolution: **1920 × 1080 (16:9)**.
2. **Audio & Pacing:**
   - Speak with steady confidence.
   - Aim for ~130–140 words per minute for optimal clarity.
3. **Cursor Movement:**
   - Rehearse the sequence once so clicks land cleanly with your narration.
   - Avoid fast circular cursor waving.
4. **Recording Tools:**
   - **OBS Studio** (free, crisp 1080p 60fps recording).
   - **Windows Game Bar** (`Win + Alt + R`).
