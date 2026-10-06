# Graph Visualizer

**Group Homework – Graph Theory Week 5**  
Institut Teknologi Sepuluh Nopember (ITS)

---

## Identity

|    NRP     |           Nama             |
| :--------: |       :------------:       |
| 5025251260 | Aqilah Ibrahim             |
| 5025251161 | Rizqi Arya Kuskhilbyano    |
| 5025251009 | Athar Rozy Rasyidan                    |
| 5025251017 | Wafi Fawwaz Sutisna                    |

---

## Prerequisites

- Python >= 3.10
- Dependencies:

```bash
pip install networkx matplotlib numpy
```

---

## How to Run

Run the main application script:

```bash
python graph_visualizer.py
```

---

## Usage

### 1. Choose Input Representation
- **Adjacency Matrix:** Square $n \times n$ matrix where entry $[i][j] = 1$ if there is an edge connecting vertex $i$ and $j$.
- **Incidence Matrix:** $n \times m$ matrix where entry $[i][j] = 1$ if vertex $i$ is incident to edge $e_j$.

### 2. Enter Matrix
- Select preset from the **Load Preset** dropdown (Slide 4, Slide 6, Slide 9, Slide 12, Slide 13), OR
- Adjust vertices ($n$) / edges ($m$), then type into the cells or click **Paste Matrix** to paste space/comma separated numbers.

### 3. Click "Visualize & Analyze"
- View the generated graph and matrix representations across the tabs.

### Tabs Overview
| Tab | Description |
|---|---|
| **Graph Visualization** | Graph topology with spanning tree branches highlighted in solid blue and chords highlighted in dashed pink. |
| **Fundamental Cycle Matrix ($B_f$)** | Displays $B_f = [I_\mu \mid B_t]$ heatmap with cycle list ($Z_1, Z_2, \dots$) and chord identifications. |
| **Cut-Set Matrix ($Q$)** | Displays fundamental cut-set matrix heatmap and equations ($S_1, S_2, \dots$). |
| **Graph Info** | Degree sequence, adjacency matrix, edge list, and bridge detection. |

---

## Sample Input / Output

### Example: AI Service Architecture (Slide 12 Exercise)

- **Vertices:** A (Image Upload), B (Preprocessing), C (Object Detection), D (Tracking), E (Database), F (Dashboard)
- **Connections:** A–B, B–C, B–E, C–D, C–E, D–E, D–F, E–F

#### Adjacency Matrix ($6 \times 6$):
```
    A  B  C  D  E  F
A   0  1  0  0  0  0
B   1  0  1  0  1  0
C   0  1  0  1  1  0
D   0  0  1  0  1  1
E   0  1  1  1  0  1
F   0  0  0  1  1  0
```

#### Output Summary:
- **Vertices:** 6, **Edges:** 8
- **Degrees:** A=1, B=3, C=3, D=3, E=4, F=2
- **Direct connections of E:** B, C, D, F (Highest degree = 4)
- **Cyclomatic number ($\mu$):** $8 - 6 + 1 = 3$ (3 fundamental cycles)
- **Critical edges (bridges):** None (graph is 2-edge-connected)

---

## AI Disclosure Statement

- AI assistance (Google Antigravity / Gemini) was used to help structure parts of the code, Tkinter GUI layout and verify matrix calculations against lecture slide examples.
<img width="961" height="677" alt="image" src="https://github.com/user-attachments/assets/6a98e9c3-d45b-4146-b41f-1d95f3b6c9c1" />
- All algorithms (spanning tree selection, fundamental cycle derivation, cut-set formation) were tested, understood, and validated by the group.
https://share.gemini.google/ArFWQW5cbWrJ
