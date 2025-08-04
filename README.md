
# Multi-Elevator Simulation and Reinforcement Learning Control

This project investigates and compares classic and AI-based strategies for optimizing elevator operations in a multi-agent environment.  
It was developed as part of a university research project, with an emphasis on practical reinforcement learning, simulation, and comparative analytics.

---

## Project Structure

- **Elevator_Scanning:**  
  Classic "scan-based" elevator control (greedy strategy).  
  Serves as baseline for evaluation.
- **Elevator_Modell_Simulation:**  
  Simulation environment using a trained reinforcement learning model (PPO).  
  Allows replay and analysis of trained policies.
- **Elevator_Reinforcement_Training:**  
  Training environment for RL agents (Stable Baselines3, Maskable PPO, SubprocVecEnv, etc.)
- **Documentation_in_german:**  
  German documentation of the training and evaluation process, with discussion of results and implementation notes.

---

## Problem Setting

- **Environment:**  
  - 3 elevators, 10 floors, up to 200 guests per episode
  - Guests spawn in the morning (exponentially distributed, ~2 per hour on average) and move between floors.
  - Each episode simulates 6–10 real-world hours (step = 1s).
- **Action Space:**  
  - For each elevator: `wait`, `up`, `down`
  - Masking ensures only valid moves (e.g., no "wait" after closing doors).
- **Rewards:**  
  - Small negative reward for each person waiting or in an elevator.
  - Larger positive reward for successful drop-off, smaller for boarding.

---

## Algorithms

- **Scanning strategy:**  
  - Elevators move continuously up and down, picking up guests as encountered.
- **Reinforcement Learning:**  
  - Maskable Proximal Policy Optimization (PPO) agent (Stable Baselines3).
  - Trained on single-elevator environments (for computational reasons).
  - Curriculum learning and parallel training with SubprocVecEnv.
  - Action masking applied to improve exploration and avoid degenerate policies.
  - PPO was chosen based on robust performance and faculty recommendations.

---

## Key Results

- **Scanning strategy:**  
  - Avg. waiting time: **47.3 s**  
  - Avg. ride time: **31.0 s**  
  - Avg. total time: **78.4 s**
- **Reinforcement learning:**  
  - Avg. waiting time: **23.9 s**  
  - Avg. ride time: **48.4 s**  
  - Avg. total time: **72.3 s**
- **Interpretation:**  
  RL agent **significantly reduced guest waiting times** at the expense of slightly longer ride times, resulting in an overall improvement of total time spent per guest.

---
## Getting Started

### Requirements

- Python 3.12.10
- All dependencies will be listed in `requirements.txt` (to be added soon)
- Stable Baselines3, sb3-contrib, Gymnasium, NumPy, Pygame, Matplotlib

### Running Experiments

- **Classic scan-based control:**  
  ```bash
  cd Elevator_Scanning
  python main.py
  ```
  
- **Simulation with RL-trained model:**

```bash
  cd Elevator_Modell_Simulation
  python main.py
```

- **Training Environment:**
  ```bash
    cd Elevator_Reinforcement_Training
    python resume_training.py
  ```


