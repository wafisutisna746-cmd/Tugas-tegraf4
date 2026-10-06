import tkinter as tk
from tkinter import messagebox
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ── parse input ──
def parse_matrix(text):
    rows = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # support space or comma separator
        vals = line.replace(",", " ").split()
        rows.append([float(v) for v in vals])
    return np.array(rows)

def adj_to_graph(M):
    G = nx.Graph()
    n = M.shape[0]
    G.add_nodes_from(range(n))
    for i in range(n):
        for j in range(i+1, n):
            if M[i,j] != 0:
                G.add_edge(i, j)
    return G

def inc_to_graph(M):
    n, m = M.shape
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for e in range(m):
        nodes = [i for i in range(n) if M[i,e] != 0]
        if len(nodes) == 2:
            G.add_edge(nodes[0], nodes[1])
    return G

def fundamental_cycle_matrix(G):
    if not nx.is_connected(G):
        G = G.subgraph(max(nx.connected_components(G), key=len)).copy()
    edges = sorted(G.edges(), key=lambda e: (min(e), max(e)))
    eidx = {(min(u,v), max(u,v)): i for i,(u,v) in enumerate(edges)}
    T = nx.minimum_spanning_tree(G)
    tree_set = {(min(u,v), max(u,v)) for u,v in T.edges()}
    chords = [(min(u,v), max(u,v)) for u,v in edges if (min(u,v),max(u,v)) not in tree_set]
    if not chords:
        return np.zeros((0, len(edges)), dtype=int), [], [f"e{i+1}({u}-{v})" for i,(u,v) in enumerate(edges)]
    B = np.zeros((len(chords), len(edges)), dtype=int)
    for r, (cu, cv) in enumerate(chords):
        path = nx.shortest_path(T, cu, cv)
        for i in range(len(path)-1):
            e = (min(path[i],path[i+1]), max(path[i],path[i+1]))
            B[r, eidx[e]] = 1
        B[r, eidx[(cu,cv)]] = 1
    row_lbl = [f"C{i+1}({u}-{v})" for i,(u,v) in enumerate(chords)]
    col_lbl = [f"e{i+1}({u}-{v})" for i,(u,v) in enumerate(edges)]
    return B, row_lbl, col_lbl

def cutset_matrix(G):
    if not nx.is_connected(G):
        G = G.subgraph(max(nx.connected_components(G), key=len)).copy()
    edges = sorted(G.edges(), key=lambda e: (min(e), max(e)))
    eidx = {(min(u,v), max(u,v)): i for i,(u,v) in enumerate(edges)}
    T = nx.minimum_spanning_tree(G)
    tree_edges = [(min(u,v), max(u,v)) for u,v in T.edges()]
    tree_set = set(tree_edges)
    chords = [(min(u,v), max(u,v)) for u,v in edges if (min(u,v),max(u,v)) not in tree_set]
    Q = np.zeros((len(tree_edges), len(edges)), dtype=int)
    for r, te in enumerate(tree_edges):
        Tc = T.copy(); Tc.remove_edge(*te)
        comps = list(nx.connected_components(Tc))
        if len(comps) < 2: continue
        S1, S2 = comps
        Q[r, eidx[te]] = 1
        for ce in chords:
            u, v = ce
            if (u in S1 and v in S2) or (u in S2 and v in S1):
                Q[r, eidx[ce]] = 1
    row_lbl = [f"D{i+1}({u}-{v})" for i,(u,v) in enumerate(tree_edges)]
    col_lbl = [f"e{i+1}({u}-{v})" for i,(u,v) in enumerate(edges)]
    return Q, row_lbl, col_lbl

# ── draw matrix as heatmap ──
def draw_matrix(ax, M, row_lbl, col_lbl, title, cmap):
    ax.set_facecolor("#f9f9f9")
    if M.size == 0:
        ax.text(0.5, 0.5, "No data\n(graph is a tree, no chords)", ha="center", va="center", fontsize=11)
        ax.set_title(title); ax.axis("off"); return
    ax.imshow(M, cmap=cmap, aspect="auto", vmin=0, vmax=1)
    for r in range(M.shape[0]):
        for c in range(M.shape[1]):
            ax.text(c, r, str(M[r,c]), ha="center", va="center", fontsize=8)
    ax.set_xticks(range(len(col_lbl))); ax.set_xticklabels(col_lbl, rotation=45, ha="right", fontsize=7)
    ax.set_yticks(range(len(row_lbl))); ax.set_yticklabels(row_lbl, fontsize=7)
    ax.set_title(title, fontsize=11, fontweight="bold")

# ── main GUI ──
def run():
    root = tk.Tk()
    root.title("Graph Visualizer – W5 Homework")
    root.geometry("900x700")

    tk.Label(root, text="Paste your matrix (rows separated by newline, values by space or comma):",
             font=("Arial", 10)).pack(anchor="w", padx=10, pady=(10,0))

    # mode selector
    mode_var = tk.StringVar(value="adjacency")
    f = tk.Frame(root); f.pack(anchor="w", padx=10)
    tk.Radiobutton(f, text="Adjacency Matrix", variable=mode_var, value="adjacency").pack(side="left")
    tk.Radiobutton(f, text="Incidence Matrix", variable=mode_var, value="incidence").pack(side="left", padx=10)

    # text input
    txt = tk.Text(root, height=8, font=("Consolas", 10), relief="solid", bd=1)
    txt.pack(fill="x", padx=10, pady=5)
    txt.insert("end",
        "0 1 0 0 0 0\n"
        "1 0 1 0 1 0\n"
        "0 1 0 1 1 0\n"
        "0 0 1 0 1 1\n"
        "0 1 1 1 0 1\n"
        "0 0 0 1 1 0"
    )

    # canvas area
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    fig.tight_layout(pad=3)
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)

    LABELS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    def analyze():
        try:
            M = parse_matrix(txt.get("1.0", "end"))
        except Exception as e:
            messagebox.showerror("Error", f"Matrix parse error:\n{e}"); return
        try:
            if mode_var.get() == "adjacency":
                G = adj_to_graph(M)
            else:
                G = inc_to_graph(M)

            n = G.number_of_nodes()
            labels = {i: LABELS[i] if i < 26 else str(i) for i in range(n)}

            for ax in axes: ax.cla()

            # --- Tab 1: Graph ---
            pos = nx.spring_layout(G, seed=42)
            if nx.is_connected(G):
                T = nx.minimum_spanning_tree(G)
                te = [(u,v) for u,v in G.edges() if T.has_edge(u,v)]
                ce = [(u,v) for u,v in G.edges() if not T.has_edge(u,v)]
                nx.draw_networkx_edges(G, pos, edgelist=te, ax=axes[0], edge_color="steelblue", width=2)
                nx.draw_networkx_edges(G, pos, edgelist=ce, ax=axes[0], edge_color="tomato", width=2, style="dashed")
            else:
                nx.draw_networkx_edges(G, pos, ax=axes[0], edge_color="steelblue", width=2)
            nx.draw_networkx_nodes(G, pos, ax=axes[0], node_color="lightgreen", node_size=600, edgecolors="black")
            nx.draw_networkx_labels(G, pos, labels=labels, ax=axes[0], font_weight="bold")
            axes[0].set_title("Graph\n(blue=tree, red dash=chord)", fontsize=11, fontweight="bold")
            axes[0].axis("off")

            # --- Tab 2: FCM ---
            B, Br, Bc = fundamental_cycle_matrix(G)
            draw_matrix(axes[1], B, Br, Bc, "Fundamental Cycle Matrix (B)", "YlOrRd")

            # --- Tab 3: Cut-Set ---
            Qm, Qr, Qc = cutset_matrix(G)
            draw_matrix(axes[2], Qm, Qr, Qc, "Cut-Set Matrix (Q)", "Blues")

            fig.tight_layout(pad=3)
            canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(root, text="▶ Visualize & Analyze", command=analyze,
              bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
              padx=12, pady=5, relief="flat", cursor="hand2").pack(pady=5)

    analyze()  # auto-run with example
    root.mainloop()

run()
