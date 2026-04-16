# 🌌 Quantum Vacuum Room — Real Physics Simulator

## 🚀 Overview

**Quantum Vacuum Room** is a real-time 3D atomic physics simulator that lets you build a universe from scratch.

You start with **pure vacuum — no forces, no motion, no energy** — and progressively enable physical laws to watch how atoms behave and interact.

This project combines:

* ⚛️ Physics simulation
* 🎮 Interactive sandbox
* 🎓 Educational visualization
* 🤖 AI-driven narration

---

## ✨ Features

### 🧪 Physics Modules (Toggle Anytime)

* **Gravity** — pulls atoms toward the floor
* **Thermal Motion** — temperature-driven kinetic energy
* **Electromagnetism** — Coulomb force between charged atoms
* **Van der Waals** — weak attraction (Lennard-Jones potential)
* **Quantum Pressure** — Pauli exclusion (prevents overlap)
* **Nuclear Decay** — Uranium/Thorium emit alpha particles

---

### ⚛️ Real Physics (Scaled for Visualization)

* Velocity Verlet integration
* Maxwell-Boltzmann velocity distribution
* Coulomb’s law (with softening for stability)
* Lennard-Jones potential
* Exponential nuclear decay law
* Momentum conservation during decay

---

### 🎨 Visual Experience

* 3D interactive Plotly rendering
* Glowing atoms with color-coded elements
* Motion trails and velocity vectors
* Shockwaves during nuclear decay
* Smooth camera motion

---

### 🤖 AI Narration System

Real-time subtitles explain what’s happening:

Examples:

* *"Uranium atom decays → alpha particle emitted → recoil affects nearby atoms"*
* *"Quantum pressure prevents atomic overlap"*
* *"Energy spike detected — system temporarily unstable"*

---

### 📊 Live Metrics Dashboard

* Atom count
* Kinetic energy
* Potential energy
* Decay events
* System stability indicators

---

## 🛠 Installation

### 1. Clone or download the project

```bash
git clone <your-repo-url>
cd quantum-vacuum-room
```

### 2. Install dependencies

```bash
pip install numpy pandas plotly streamlit
```

---

## ▶️ Run the Simulator

```bash
streamlit run your_file.py
```

Then open your browser at:

```
http://localhost:8501
```

---

## 🎮 Controls

### Sidebar

* Toggle physics modules
* Adjust temperature
* Add atoms
* Load presets
* Reset simulation

### Presets

* Noble gases
* Organic mix
* Metals
* Radioactive set
* All elements

---

## 🧠 How It Works

### Simulation Loop

1. Compute forces (Coulomb, LJ, Pauli, etc.)
2. Integrate motion (Velocity Verlet)
3. Apply thermostat (thermal motion)
4. Handle decay events
5. Update visuals + narration

---

### Nuclear Decay

* Uses exponential probability:

  ```
  P = 1 - exp(-λΔt)
  λ = ln(2) / half-life
  ```

* Emits alpha particle (He nucleus)

* Parent atom recoils (momentum conservation)

* Generates shockwave visualization

---

## ⚡ Performance Notes

* Optimized for ~50–100 atoms
* Uses capped interaction radius
* Includes stability controls to prevent simulation blow-up

---

## 🧯 Stability Features

* Force clamping
* Velocity damping
* Minimum distance cutoff
* Adaptive timestep
* Energy spike detection

---

## 🔮 Future Ideas

* Molecular bonding (chemistry engine)
* GPU acceleration
* Quantum wavefunction visualization
* Electron orbitals
* Relativistic effects

---

## 🎯 Goal

To create:

> *A living, interactive universe where physics emerges from nothing — and you can watch it happen in real time.*

---

## 👨‍💻 Author

Built as an advanced physics + visualization experiment combining simulation, UI/UX, and AI narration.

---

## ⚠️ Disclaimer

This is a **visual and educational simulation**, not a fully accurate quantum or nuclear physics engine. Real-world physics is far more complex.

---

Enjoy building your own universe 🌌
