# SilentBridge

SilentBridge is an AI-powered smart wearable communication system designed to help deaf and speech-impaired individuals communicate naturally in real time using sign language recognition, subtitles, and speech generation.

The system uses a smart glove equipped with Hall Effect sensors and motion tracking to detect hand gestures and convert them into text and voice output through a connected mobile application.

---

# Problem Statement

Millions of deaf and speech-impaired individuals face communication barriers in daily life due to limited accessibility tools and dependency on interpreters.

Most existing sign-language systems:
- support only limited gestures
- require expensive hardware
- depend heavily on cameras
- lack portability
- fail in real-world environments

SilentBridge aims to provide a portable, low-cost, real-time communication assistant that works using wearable sensors instead of camera-based tracking.

---

# Features

- Real-time sign language recognition
- Subtitle generation on mobile device
- Text-to-speech conversion
- BLE-based wireless communication
- Wearable smart glove architecture
- Camera-free operation
- Motion-aware gesture detection
- Lightweight and portable design
- Expandable AI pipeline for future learning models

---

# System Architecture

text Hall Sensors + MPU6050             ↓          ESP32             ↓       Bluetooth BLE             ↓        Mobile App             ↓  Subtitles + Speech Output 

---

# Hardware Components

| Component | Purpose |
|---|---|
| ESP32 DevKit | Main controller and BLE communication |
| SS49E Hall Sensors | Finger bend detection |
| Neodymium Magnets | Magnetic field generation |
| MPU6050 | Motion and orientation tracking |
| 10kΩ Resistors | Signal stabilization |
| Li-ion Battery | Portable power supply |
| TP4056 Module | Battery charging and protection |
| Lycra Glove | Wearable mounting base |

---

# Software Stack

| Technology | Purpose |
|---|---|
| Arduino IDE | ESP32 programming |
| Flutter | Mobile application |
| Python | Data processing and AI pipeline |
| TensorFlow | Gesture classification |
| BLE Communication | Wireless data transfer |
| Text-to-Speech Engine | Voice generation |

---

# Working Principle

1. Finger movements change the distance between Hall sensors and magnets.
2. Hall sensors generate analog values based on magnetic field variation.
3. MPU6050 captures hand orientation and movement dynamics.
4. ESP32 reads all sensor values and processes gesture patterns.
5. Recognized gestures are sent to the mobile app using BLE.
6. The mobile application displays subtitles and generates speech output.

---

# Example Data Flow

json {   "gesture": "HELP",   "confidence": 0.94 } 

---

# Development Roadmap

## Phase 1
- Sensor calibration
- Stable gesture detection
- BLE communication

## Phase 2
- Static gesture recognition
- Subtitle display
- Speech generation

## Phase 3
- Dynamic gesture recognition
- AI-based classification
- Context-aware translation

## Phase 4
- Personalized gesture learning
- Emergency communication mode
- Multilingual support

---

# Applications

- Daily communication assistance
- Educational accessibility
- Hospitals and emergency situations
- Smart accessibility systems
- Human-computer interaction research

---

# Future Scope

- Continuous sentence recognition
- AI-driven contextual translation
- Offline edge AI processing
- Smartwatch integration
- AR subtitle systems
- Personalized adaptive gesture learning
- Multilingual sign translation

---

# Why SilentBridge

SilentBridge focuses on practical deployment instead of only academic demonstration.

The system is:
- portable
- wearable
- scalable
- low-cost
- privacy-friendly
- real-time

Unlike camera-dependent systems, SilentBridge can operate naturally in real-world environments without requiring users to remain inside a fixed camera frame.

---

# Project Status

Current Stage:
Prototype Development

Modules Completed:
- Hardware planning
- System architecture
- Sensor selection
- Communication pipeline design

In Progress:
- Sensor calibration
- ESP32 integration
- BLE communication
- Gesture dataset collection

---

# Team Vision

SilentBridge aims to bridge the communication gap between deaf or speech-impaired individuals and the world around them using affordable AI-powered wearable technology.

The goal is to create a practical and deployable assistive communication platform rather than a traditional academic prototype.

---

# License

This project is licensed under the MIT License.

---

# Contributors

Developed by the SilentBridge Team.
