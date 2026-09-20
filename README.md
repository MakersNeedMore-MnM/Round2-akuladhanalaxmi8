
# AquaGrid – FloodPulse

## Urban Flood Nowcasting System – Drainage and Rainfall Coupling

---

## Overview

**AquaGrid – FloodPulse** is an Urban Flood Nowcasting System designed to provide localized flood predictions by coupling **rainfall, terrain, and drainage-network information**.

The system addresses a major limitation of conventional flood warning approaches: flooding can vary significantly from one street or locality to another depending on terrain, rainfall, drainage capacity, and water accumulation.

FloodPulse aims to provide a **0–3 hour flood nowcast** by combining rainfall nowcasting with runoff estimation, DEM-based surface routing, drainage-network capacity analysis, and surface water storage.

The final output is a **Flood Depth Map** that can be presented through a GIS dashboard and used for alerts and Safe Route services.

---

# Problem Statement

### Urban Flood Nowcasting System – Drainage and Rainfall Coupling

Urban flooding is not determined by rainfall alone.

Even when rainfall is known, the actual flood situation depends on:

- Local terrain
- Surface runoff
- Drainage-network capacity
- Drainage inflow
- Water accumulation
- Localized low-lying areas

FloodPulse addresses this by coupling:

**Rainfall + Terrain + Drainage**

to estimate potential flooding over the next **0–3 hours**.

---

# Proposed Solution

FloodPulse follows a coupled **Rainfall–Terrain–Drainage** approach.

The system receives rainfall information and drainage observations, processes them with terrain and drainage-network information, and estimates where water may accumulate.

The core pipeline is:

Rainfall Nowcast
       ↓
Runoff Estimation
       ↓
DEM Surface Routing
       ↓
Pooling Zones
       ↓
Drainage Capacity vs Inflow
       ↓
Excess Water Volume
       ↓
DEM Surface Storage / Ponding
       ↓
Fusion Engine
       ↓
Flood Depth Map
       ↓
GIS Dashboard / Alerts / Safe Route API


# System Architecture


┌─────────────────────────────┐
│ Doppler Radar / IMD Feed    │
│ Rainfall Data               │
└──────────────┬──────────────┘
               │
               ↓
┌─────────────────────────────┐
│ Rainfall Nowcast            │
└──────────────┬──────────────┘
               │
               ↓
┌─────────────────────────────┐
│ Runoff Estimation           │
└──────────────┬──────────────┘
               │
               ↓
┌─────────────────────────────┐
│ DEM Surface Routing         │
└──────────────┬──────────────┘
               │
               ↓
┌─────────────────────────────┐
│ Pooling Zones               │
└──────────────┬──────────────┘
               │
               ↓
┌─────────────────────────────┐
│ Drainage Graph              │
│ Capacity vs Inflow          │
└──────────────┬──────────────┘
               │
               ↓
┌─────────────────────────────┐
│ Excess Water Volume         │
└──────────────┬──────────────┘
               │
               ↓
┌─────────────────────────────┐
│ DEM Surface Storage /       │
│ Ponding                     │
└──────────────┬──────────────┘
               │
               ↓
┌─────────────────────────────┐
│ Fusion Engine               │
└──────────────┬──────────────┘
               │
               ↓
┌─────────────────────────────┐
│ Flood Depth Map             │
│ 0–3 Hour Nowcast            │
└──────────────┬──────────────┘
               │
        ┌──────┴───────┐
        ↓              ↓
┌──────────────┐  ┌──────────────────┐
│ GIS Dashboard│  │ Alerts /         │
│              │  │ Safe Route API   │
└──────────────┘  └──────────────────┘

# Input Data

## 1. Rainfall Data

The architecture is designed to receive rainfall information from sources such as:

* Doppler Radar
* IMD rainfall feeds

Rainfall information forms the primary input for the rainfall nowcasting stage.

## 2. Drain Sensor Data

Drain sensors provide field-level information about drainage conditions.

These observations can be incorporated into the drainage analysis along with rainfall and terrain information.

## 3. Digital Elevation Model (DEM)

DEM data provides terrain information required for:

* Surface routing
* Flow direction
* Low-lying area identification
* Water accumulation analysis
* Surface storage estimation

## 4. Drainage Network

The drainage system is represented as a network/graph.

The system analyzes:


Drainage Inflow
       vs
Drainage Capacity


This helps identify locations where incoming water may exceed the available drainage capacity.

---

# Technical Approach

## 1. Rainfall Nowcast

Rainfall information from the available input source is processed to generate a short-term rainfall nowcast.

The system focuses on the **0–3 hour prediction window**.

## 2. Runoff Estimation

The rainfall nowcast is converted into estimated surface runoff.

This provides an estimate of the amount of water that may contribute to surface flow and drainage inflow.

## 3. DEM Surface Routing

The Digital Elevation Model is used to determine how runoff can move across the terrain.

Surface routing helps identify potential water-flow paths and areas where water may accumulate.

## 4. Pooling Zone Identification

Terrain characteristics are used to identify potential pooling zones.

These are locations where the surface geometry can cause water to accumulate.

## 5. Drainage Capacity vs Inflow

The drainage network is analyzed by comparing the estimated inflow with available drainage capacity.


Drainage Capacity < Incoming Flow
                ↓
        Potential Excess Water

This coupling is an important part of the system because flooding depends not only on rainfall but also on whether the drainage network can handle the resulting inflow.

## 6. Excess Water Volume

When drainage capacity is insufficient compared with inflow, excess water volume is estimated.

This excess water becomes an input for surface storage and ponding analysis.

## 7. DEM Surface Storage / Ponding

The excess water is considered together with terrain information to estimate surface storage and ponding.

This helps determine potential flood depth and affected areas.

## 8. Fusion Engine

The Fusion Engine combines the outputs of the rainfall, terrain, and drainage components.

The main information brought together includes:

* Rainfall nowcast
* Runoff estimation
* DEM surface routing
* Pooling zones
* Drainage capacity
* Drainage inflow
* Excess water
* Surface storage / ponding

The resulting information is used to generate the flood-depth output.

---

# Flood Depth Map

The primary output of FloodPulse is a:

### **0–3 Hour Flood Depth Map**

The map is intended to provide localized information about potential flood depth and affected areas.

This output can support:

* Flood monitoring
* Emergency response
* Localized warnings
* Drainage intervention
* Route planning

---

# GIS Dashboard

The predicted flood information can be visualized through a GIS-based dashboard.

The dashboard is intended to provide a spatial representation of:

* Flood depth
* Potentially affected areas
* Pooling zones
* Drainage information
* Flood-prone locations

---

# Alerts

FloodPulse can provide alerts based on the generated flood information.

Alerts can help communicate potential flooding to relevant users and support timely response.

---

# Safe Route API

The flood-depth output can also be used by a Safe Route API.

The concept is:

Flood Depth Map
       ↓
Identify Affected Roads
       ↓
Evaluate Route Conditions
       ↓
Provide Safer Route Information


This allows the flood prediction output to be connected to route-level decision support.

---

# Smart Drainage Component

The project also includes a drainage-focused implementation involving **AI-based detection and hardware integration**.

This component explores the use of camera-based detection, waste counting, ESP32 communication, and servo-based mechanisms for drainage-related monitoring and automation.

The implementation is organized into multiple development phases.

---

# AI-Based Detection

Camera input can be processed using a trained computer-vision model to identify relevant objects.

The detection pipeline includes:

Camera Input
      ↓
AI Model
      ↓
Object Detection
      ↓
Detection Results
      ↓
Waste Counting


# Waste Counting

The detected objects can be processed to calculate the number of detected items.

This provides information that can be used by the downstream system.

---

# ESP32 Communication

The Python-side implementation communicates with an ESP32 through serial communication.

Python Application
       ↓
Detection Information
       ↓
Serial Communication
       ↓
ESP32

# Servo-Based Hardware Integration

The ESP32 implementation includes servo control for the hardware-side mechanism.

The basic workflow is:

Detection Result
       ↓
Python Processing
       ↓
ESP32
       ↓
Servo Control

# Project Implementation

The repository contains the implementation developed for the AI detection, communication, hardware integration, and final integration stages.

## Phase 1 – Object Detection

Development of the AI-based object detection component.

## Phase 2 – Dataset Preparation

Preparation and preprocessing of the dataset used for the AI detection component.

## Phase 3 – Model Training

Training and development of the detection model using the prepared dataset.

## Phase 4 – Real-Time Detection

Integration of camera input with the detection system for real-time processing.

## Phase 5 – Waste Counting

Processing detection results to count the detected objects.

## Phase 6 – ESP32 Communication


phase6_esp32_communication/
│
├── esp32_receiver.ino
├── python_sender.py
├── requirements.txt
└── run_sender.bat


## Phase 7 – Servo Sorting


phase7_servo_sorting/
│
├── esp32_servo_sorting.ino
└── servo_test.ino


 Phase 8 – Final Integration

phase8_final_integration/
│
├── main_final.py
├── count_utils.py
├── serial_controller.py
├── test_cameras.py
├── requirements.txt
└── run_final.bat

# Repository Structure


AquaGrid / FloodPulse
│
├── phase1_object_detection/
├── phase2_dataset_prep/
├── phase3_model_training/
├── phase4_webcam_detection/
├── phase5_waste_counting/
│
├── phase6_esp32_communication/
│   ├── esp32_receiver.ino
│   ├── python_sender.py
│   ├── requirements.txt
│   └── run_sender.bat
│
├── phase7_servo_sorting/
│   ├── esp32_servo_sorting.ino
│   └── servo_test.ino
│
└── phase8_final_integration/
    ├── main_final.py
    ├── count_utils.py
    ├── serial_controller.py
    ├── test_cameras.py
    ├── requirements.txt
    └── run_final.bat


# Figma Prototype

The project workflow and interface prototype are available through Figma.

### Figma Prototype

[https://pure-trek-02236205.figma.site/](https://pure-trek-02236205.figma.site/)

---

# Prototype & Demonstration Status

The current prototype/demo uses **simulated rainfall and sensor inputs** for demonstrating the system workflow.

The architecture is designed for direct integration with:

* IMD/radar rainfall data
* Real drainage sensors
* Field-level observations
* Actual drainage-network information

The prototype demonstrates the proposed processing and integration workflow, while the architecture is designed to support real-world deployment.

---

# Implementation Status

The project includes implementation for:

* AI-based object detection
* Real-time camera detection
* Waste counting
* ESP32 communication
* Servo control
* Final integration

Due to the high storage requirements of the complete dataset and generated model files, the full raw dataset and large model artifacts are not included in the GitHub repository.

The important implementation and hardware-integration code has been pushed to the assigned repository.

---

# Technology Stack

## AI / Computer Vision

* Python
* Machine Learning
* Deep Learning
* Computer Vision
* OpenCV

## Flood & Geospatial Processing

* Rainfall Nowcasting
* Digital Elevation Model (DEM)
* Surface Routing
* Drainage Network Analysis
* Flood Depth Estimation
* GIS

## IoT & Hardware

* ESP32
* Drain Sensors
* Servo Motors
* Serial Communication
* Camera

## Application Layer

* Python
* Dashboard / Visualization
* API Integration

---

# Future Scope

The system can be extended with:

* Direct IMD/radar feed integration
* Real-time rainfall data
* Real drainage sensor deployment
* Larger-scale drainage-network datasets
* Real-time flood-depth updates
* Improved rainfall nowcasting
* Real-world city-scale deployment
* Mobile notifications
* Advanced route optimization
* Historical flood-data analysis
* Continuous AI model improvement

---

# Key Innovation

The core concept of FloodPulse is to move beyond rainfall-only flood prediction by coupling:


RAIN
  +
TERRAIN
  +
DRAINAGE
  +
FIELD INFORMATION
  ↓
FLOOD NOWCAST


The system connects rainfall information with terrain and drainage-network conditions to estimate how rainfall may translate into localized surface flooding.

---

# Project Vision

### From Reactive Flood Response to Predictive Urban Flood Intelligence

AquaGrid – FloodPulse aims to provide localized and actionable flood information by connecting rainfall, terrain, drainage infrastructure, and field observations into a unified flood-nowcasting workflow.

---

# Project

## AquaGrid – FloodPulse

### Urban Flood Nowcasting System – Drainage and Rainfall Coupling

**Figma Prototype:**
[https://pure-trek-02236205.figma.site/](https://pure-trek-02236205.figma.site/)

```
```
