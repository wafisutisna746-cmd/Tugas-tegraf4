"""
Graph Visualizer
Group Homework - Graph Theory Week 5
Institut Teknologi Sepuluh Nopember (ITS)
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.patches as mpatches

# --- Graph Math Helpers ---

def adj_to_graph(adj: np.ndarray) -> tuple[nx.Graph, list[tuple[int, int, str]]]:
    """Convert an adjacency matrix (n x n) into a networkx Graph and edge list."""
    n = adj.shape[0]
    G = nx.Graph()
    G.add_nodes_from(range(n))
    edges = []
    e_counter = 1
    for i in range(n):
        for j in range(i + 1, n):
            if adj[i, j] != 0:
                G.add_edge(i, j, weight=adj[i, j])
                edges.append((i, j, f"e{e_counter}"))
                e_counter += 1
    return G, edges


def incidence_to_graph(inc: np.ndarray) -> tuple[nx.Graph, list[tuple[int, int, str]], np.ndarray]:
    """Convert an incidence matrix (n x m) into a graph, edge list, and adjacency matrix."""
    n, m = inc.shape
    G = nx.Graph()
    G.add_nodes_from(range(n))
    adj = np.zeros((n, n), dtype=float)
    edges = []

    for c in range(m):
        col = inc[:, c]
        nodes = np.where(col != 0)[0]
        label = f"e{c + 1}"
        if len(nodes) == 2:
            u, v = int(nodes[0]), int(nodes[1])
            G.add_edge(u, v)
            adj[u, v] = 1
            adj[v, u] = 1
            edges.append((u, v, label))
        elif len(nodes) == 1:
            u = int(nodes[0])
            adj[u, u] = 1
            edges.append((u, u, label))

    return G, edges, adj


def compute_fundamental_cycle_matrix(G: nx.Graph, edge_list: list) -> tuple[np.ndarray, list, list, list, list]:
    """
    Computes Fundamental Cycle Matrix B_f = [I | B_t].
    Columns ordered as: [chords | tree_edges].
    """
    if G.number_of_nodes() == 0 or G.number_of_edges() == 0:
        return np.zeros((0, 0), dtype=int), [], [], [], []

    if not nx.is_connected(G):
        largest_cc = max(nx.connected_components(G), key=len)
        G = G.subgraph(largest_cc).copy()

    # Identify spanning tree
    T = nx.minimum_spanning_tree(G)
    tree_set = {tuple(sorted((u, v))) for u, v in T.edges()}

    # Separate tree edges and chords
    tree_edges = []
    chord_edges = []
    for u, v, lbl in edge_list:
        pair = tuple(sorted((u, v)))
        if pair in tree_set and pair not in [t[:2] for t in tree_edges]:
            tree_edges.append((pair[0], pair[1], lbl))
        else:
            chord_edges.append((pair[0], pair[1], lbl))

    # Column ordering: chords first (for Identity submatrix), then tree edges
    ordered_edges = chord_edges + tree_edges
    edge_index = {e[2]: idx for idx, e in enumerate(ordered_edges)}

    m = len(ordered_edges)
    k = len(chord_edges)
    B = np.zeros((k, m), dtype=int)

    cycle_labels = []
    for row_idx, (cu, cv, clbl) in enumerate(chord_edges):
        try:
            path = nx.shortest_path(T, cu, cv)
        except nx.NetworkXNoPath:
            continue

        # Chord itself is in cycle
        B[row_idx, edge_index[clbl]] = 1
        cycle_edges_str = [clbl]

        # Tree edges along the path
        for i in range(len(path) - 1):
            p_edge = tuple(sorted((path[i], path[i + 1])))
            for tu, tv, tlbl in tree_edges:
                if (tu, tv) == p_edge:
                    B[row_idx, edge_index[tlbl]] = 1
                    cycle_edges_str.append(tlbl)
                    break

        cycle_labels.append(f"Z{row_idx + 1} ({', '.join(sorted(cycle_edges_str))})")

    col_labels = [e[2] for e in ordered_edges]
    return B, cycle_labels, col_labels, tree_edges, chord_edges


def compute_cutset_matrix(G: nx.Graph, edge_list: list) -> tuple[np.ndarray, list, list]:
    """
    Computes Fundamental Cut-Set Matrix Q = [C_c | I].
    Each tree edge defines a cut-set disconnecting the spanning tree.
    """
    B, cycle_labels, col_labels, tree_edges, chord_edges = compute_fundamental_cycle_matrix(G, edge_list)
    if len(tree_edges) == 0:
        return np.zeros((0, 0), dtype=int), [], []

    T = nx.minimum_spanning_tree(G)
    ordered_edges = chord_edges + tree_edges
    edge_index = {e[2]: idx for idx, e in enumerate(ordered_edges)}

    num_tree = len(tree_edges)
    m = len(ordered_edges)
    Q = np.zeros((num_tree, m), dtype=int)
    cut_labels = []

    for row_idx, (tu, tv, tlbl) in enumerate(tree_edges):
        T_copy = T.copy()
        T_copy.remove_edge(tu, tv)
        comps = list(nx.connected_components(T_copy))
        if len(comps) < 2:
            continue
        S1, S2 = comps[0], comps[1]

        # Tree edge itself is always in cut-set
        Q[row_idx, edge_index[tlbl]] = 1
        cut_edges_str = [tlbl]

        # Check which chords cross S1 and S2
        for cu, cv, clbl in chord_edges:
            if (cu in S1 and cv in S2) or (cu in S2 and cv in S1):
                Q[row_idx, edge_index[clbl]] = 1
                cut_edges_str.append(clbl)

        cut_labels.append(f"S{row_idx + 1} ({', '.join(sorted(cut_edges_str))})")

    return Q, cut_labels, col_labels


# --- Presets from Lecture Slides ---

PRESETS = {
    "Slide 12: AI Service (6 nodes, 8 edges)": {
        "type": "adjacency",
        "n": 6, "m": 8,
        "matrix": [
            [0, 1, 0, 0, 0, 0],
            [1, 0, 1, 0, 1, 0],
            [0, 1, 0, 1, 1, 0],
            [0, 0, 1, 0, 1, 1],
            [0, 1, 1, 1, 0, 1],
            [0, 0, 0, 1, 1, 0],
        ]
    },
    "Slide 4: Undirected Graph (5 nodes)": {
        "type": "adjacency",
        "n": 5, "m": 8,
        "matrix": [
            [0, 1, 0, 1, 1],
            [1, 0, 1, 1, 1],
            [0, 1, 0, 0, 1],
            [1, 1, 0, 0, 1],
            [1, 1, 1, 1, 0],
        ]
    },
    "Slide 6: Incidence Matrix (5 nodes, 8 edges)": {
        "type": "incidence",
        "n": 5, "m": 8,
        "matrix": [
            [1, 1, 1, 0, 0, 0, 0, 0],
            [1, 0, 0, 1, 0, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 1, 1],
            [0, 1, 0, 1, 1, 0, 0, 0],
            [0, 0, 1, 0, 1, 1, 0, 1],
        ]
    },
    "Slide 9: Fundamental Cycles (5 nodes, 7 edges)": {
        "type": "incidence",
        "n": 5, "m": 7,
        "matrix": [
            [0, 0, 0, 1, 1, 0, 1],
            [0, 1, 1, 1, 0, 0, 0],
            [1, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 1, 0],
            [1, 0, 1, 0, 0, 1, 1],
        ]
    },
    "Slide 13: Data Centers Network (5 nodes, 6 edges)": {
        "type": "adjacency",
        "n": 5, "m": 6,
        "matrix": [
            [0, 1, 1, 0, 0],
            [1, 0, 1, 1, 0],
            [1, 1, 0, 0, 1],
            [0, 1, 0, 0, 1],
            [0, 0, 1, 1, 0],
        ]
    }
}

VERTEX_LABELS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


# --- Main Application ---

class GraphVisualizerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Graph Visualizer - ITS Graph Theory Week 5")
        self.geometry("1360x800")
        self.minsize(1000, 650)
        self.configure(bg="#1e1e2e")

        self._setup_style()
        self._build_ui()

        # Load initial preset
        self._load_preset("Slide 12: AI Service (6 nodes, 8 edges)")

    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Catppuccin mocha palette
        style.configure("TNotebook", background="#1e1e2e", borderwidth=0)
        style.configure("TNotebook.Tab", background="#313244", foreground="#cdd6f4",
                        padding=[14, 6], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", "#89b4fa")],
                  foreground=[("selected", "#1e1e2e")])
        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        style.configure("TButton", background="#89b4fa", foreground="#1e1e2e", font=("Segoe UI", 10, "bold"), padding=5)
        style.map("TButton", background=[("active", "#b4befe")])

    def _build_ui(self):
        # Header bar
        header = tk.Frame(self, bg="#181825", pady=8, padx=16)
        header.pack(fill=tk.X)
        tk.Label(header, text="Graph Visualizer", bg="#181825", fg="#89b4fa",
                 font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)
        tk.Label(header, text="Graph Theory Week 5 | Institut Teknologi Sepuluh Nopember (ITS)",
                 bg="#181825", fg="#6c7086", font=("Segoe UI", 10)).pack(side=tk.RIGHT)

        # Paned layout
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg="#1e1e2e", sashwidth=5, sashrelief=tk.RAISED)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Left controls panel
        left_panel = tk.Frame(paned, bg="#1e1e2e", width=420)
        paned.add(left_panel, minsize=380)
        self._build_left_panel(left_panel)

        # Right tabs panel
        right_panel = tk.Frame(paned, bg="#1e1e2e")
        paned.add(right_panel, minsize=550)
        self._build_right_panel(right_panel)

    def _build_left_panel(self, parent):
        # 1. Preset selector
        preset_frame = tk.LabelFrame(parent, text=" Load Preset ", bg="#1e1e2e", fg="#89b4fa",
                                     font=("Segoe UI", 9, "bold"), padx=8, pady=6)
        preset_frame.pack(fill=tk.X, padx=4, pady=(0, 6))

        self.preset_combo = ttk.Combobox(preset_frame, values=list(PRESETS.keys()), state="readonly")
        self.preset_combo.pack(fill=tk.X, pady=2)
        self.preset_combo.bind("<<ComboboxSelected>>", lambda e: self._load_preset(self.preset_combo.get()))

        # 2. Input type selector
        type_frame = tk.LabelFrame(parent, text=" Input Type ", bg="#1e1e2e", fg="#89b4fa",
                                   font=("Segoe UI", 9, "bold"), padx=8, pady=6)
        type_frame.pack(fill=tk.X, padx=4, pady=(0, 6))

        self.matrix_type = tk.StringVar(value="adjacency")
        r_adj = tk.Radiobutton(type_frame, text="Adjacency Matrix (n x n)", variable=self.matrix_type,
                               value="adjacency", bg="#1e1e2e", fg="#cdd6f4", selectcolor="#313244",
                               activebackground="#1e1e2e", font=("Segoe UI", 9), command=self._on_type_changed)
        r_inc = tk.Radiobutton(type_frame, text="Incidence Matrix (n x m)", variable=self.matrix_type,
                               value="incidence", bg="#1e1e2e", fg="#cdd6f4", selectcolor="#313244",
                               activebackground="#1e1e2e", font=("Segoe UI", 9), command=self._on_type_changed)
        r_adj.pack(anchor="w")
        r_inc.pack(anchor="w")

        # 3. Size controls
        size_frame = tk.Frame(parent, bg="#1e1e2e")
        size_frame.pack(fill=tk.X, padx=4, pady=4)

        tk.Label(size_frame, text="Vertices (n):", bg="#1e1e2e", fg="#cdd6f4").pack(side=tk.LEFT)
        self.n_var = tk.IntVar(value=6)
        ttk.Spinbox(size_frame, from_=2, to=15, textvariable=self.n_var, width=4,
                    command=self._rebuild_grid).pack(side=tk.LEFT, padx=(4, 10))

        tk.Label(size_frame, text="Edges (m):", bg="#1e1e2e", fg="#cdd6f4").pack(side=tk.LEFT)
        self.m_var = tk.IntVar(value=8)
        self.m_spin = ttk.Spinbox(size_frame, from_=1, to=30, textvariable=self.m_var, width=4,
                                  command=self._rebuild_grid)
        self.m_spin.pack(side=tk.LEFT, padx=4)
        self.m_spin.configure(state="disabled")

        ttk.Button(size_frame, text="Resize", command=self._rebuild_grid).pack(side=tk.RIGHT, padx=4)

        # 4. Scrollable matrix grid
        grid_container = tk.Frame(parent, bg="#1e1e2e")
        grid_container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        canvas = tk.Canvas(grid_container, bg="#1e1e2e", highlightthickness=0)
        vbar = ttk.Scrollbar(grid_container, orient=tk.VERTICAL, command=canvas.yview)
        hbar = ttk.Scrollbar(grid_container, orient=tk.HORIZONTAL, command=canvas.xview)
        canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(fill=tk.BOTH, expand=True)

        self.grid_inner = tk.Frame(canvas, bg="#1e1e2e")
        self.grid_window = canvas.create_window((0, 0), window=self.grid_inner, anchor="nw")
        self.grid_canvas = canvas
        self.grid_inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self.entries = []
        self._rebuild_grid()

        # 5. Buttons
        btn_bar = tk.Frame(parent, bg="#1e1e2e")
        btn_bar.pack(fill=tk.X, padx=4, pady=6)

        ttk.Button(btn_bar, text="Clear", command=self._clear_grid).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_bar, text="Paste Matrix", command=self._paste_matrix_dialog).pack(side=tk.LEFT, padx=2)

        run_btn = tk.Button(btn_bar, text="Visualize & Analyze", bg="#a6e3a1", fg="#1e1e2e",
                            font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=12, pady=4,
                            cursor="hand2", command=self._run)
        run_btn.pack(side=tk.RIGHT, padx=2)

        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(parent, textvariable=self.status_var, bg="#181825", fg="#a6e3a1",
                 font=("Consolas", 9), anchor="w").pack(fill=tk.X, side=tk.BOTTOM)

    def _build_right_panel(self, parent):
        self.nb = ttk.Notebook(parent)
        self.nb.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Graph visualization
        self.tab_graph = ttk.Frame(self.nb)
        self.nb.add(self.tab_graph, text="  Graph Visualization  ")

        self.fig_graph = Figure(figsize=(7, 5), dpi=96)
        self.fig_graph.patch.set_facecolor("#1e1e2e")
        self.canvas_graph = FigureCanvasTkAgg(self.fig_graph, master=self.tab_graph)
        self.canvas_graph.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Tab 2: Fundamental Cycle Matrix
        self.tab_fcm = ttk.Frame(self.nb)
        self.nb.add(self.tab_fcm, text="  Fundamental Cycle Matrix (B_f)  ")

        fcm_paned = tk.PanedWindow(self.tab_fcm, orient=tk.VERTICAL, bg="#1e1e2e", sashwidth=4)
        fcm_paned.pack(fill=tk.BOTH, expand=True)

        self.fig_fcm = Figure(figsize=(7, 3.5), dpi=96)
        self.fig_fcm.patch.set_facecolor("#1e1e2e")
        self.canvas_fcm = FigureCanvasTkAgg(self.fig_fcm, master=fcm_paned)
        fcm_paned.add(self.canvas_fcm.get_tk_widget(), minsize=220)

        self.fcm_text = tk.Text(fcm_paned, height=6, bg="#181825", fg="#cdd6f4", font=("Consolas", 10), relief=tk.FLAT)
        fcm_paned.add(self.fcm_text, minsize=100)

        # Tab 3: Cut-Set Matrix
        self.tab_csm = ttk.Frame(self.nb)
        self.nb.add(self.tab_csm, text="  Cut-Set Matrix (Q)  ")

        csm_paned = tk.PanedWindow(self.tab_csm, orient=tk.VERTICAL, bg="#1e1e2e", sashwidth=4)
        csm_paned.pack(fill=tk.BOTH, expand=True)

        self.fig_csm = Figure(figsize=(7, 3.5), dpi=96)
        self.fig_csm.patch.set_facecolor("#1e1e2e")
        self.canvas_csm = FigureCanvasTkAgg(self.fig_csm, master=csm_paned)
        csm_paned.add(self.canvas_csm.get_tk_widget(), minsize=220)

        self.csm_text = tk.Text(csm_paned, height=6, bg="#181825", fg="#cdd6f4", font=("Consolas", 10), relief=tk.FLAT)
        csm_paned.add(self.csm_text, minsize=100)

        # Tab 4: Graph Info
        self.tab_info = ttk.Frame(self.nb)
        self.nb.add(self.tab_info, text="  Graph Info  ")

        info_scroll = ttk.Scrollbar(self.tab_info)
        info_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text = tk.Text(self.tab_info, bg="#181825", fg="#cdd6f4", font=("Consolas", 10),
                                 wrap=tk.WORD, relief=tk.FLAT, yscrollcommand=info_scroll.set)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        info_scroll.configure(command=self.info_text.yview)

    # --- Grid Management ---

    def _rebuild_grid(self):
        for widget in self.grid_inner.winfo_children():
            widget.destroy()

        n = self.n_var.get()
        mtype = self.matrix_type.get()
        cols = n if mtype == "adjacency" else self.m_var.get()

        # Column header
        tk.Label(self.grid_inner, text="", bg="#1e1e2e", width=4).grid(row=0, column=0)
        for c in range(cols):
            lbl = VERTEX_LABELS[c] if mtype == "adjacency" else f"e{c+1}"
            tk.Label(self.grid_inner, text=lbl, bg="#1e1e2e", fg="#89b4fa",
                     font=("Consolas", 10, "bold"), width=4).grid(row=0, column=c+1)

        self.entries = []
        for r in range(n):
            r_lbl = VERTEX_LABELS[r]
            tk.Label(self.grid_inner, text=r_lbl, bg="#1e1e2e", fg="#89b4fa",
                     font=("Consolas", 10, "bold"), width=4).grid(row=r+1, column=0, sticky="e")
            row_entries = []
            for c in range(cols):
                e = tk.Entry(self.grid_inner, width=4, justify="center", font=("Consolas", 10),
                             bg="#313244", fg="#cdd6f4", insertbackground="#cdd6f4",
                             relief=tk.FLAT, highlightthickness=1, highlightbackground="#45475a",
                             highlightcolor="#89b4fa")
                e.insert(0, "0")
                e.grid(row=r+1, column=c+1, padx=2, pady=2)
                row_entries.append(e)
            self.entries.append(row_entries)

        self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))

    def _on_type_changed(self):
        if self.matrix_type.get() == "incidence":
            self.m_spin.configure(state="normal")
        else:
            self.m_spin.configure(state="disabled")
        self._rebuild_grid()

    def _clear_grid(self):
        for row in self.entries:
            for e in row:
                e.delete(0, tk.END)
                e.insert(0, "0")

    def _paste_matrix_dialog(self):
        text = simpledialog.askstring("Paste Matrix", "Paste matrix data (space or comma separated):")
        if not text:
            return
        lines = [line.strip().replace(",", " ").split() for line in text.strip().splitlines() if line.strip()]
        if not lines:
            return
        rows = len(lines)
        cols = len(lines[0])
        self.n_var.set(rows)
        if self.matrix_type.get() == "incidence":
            self.m_var.set(cols)
        self._rebuild_grid()
        for r in range(rows):
            for c in range(min(cols, len(self.entries[r]))):
                self.entries[r][c].delete(0, tk.END)
                self.entries[r][c].insert(0, lines[r][c])

    def _load_preset(self, name):
        if name not in PRESETS:
            return
        p = PRESETS[name]
        self.preset_combo.set(name)
        self.matrix_type.set(p["type"])
        self.n_var.set(p["n"])
        self.m_var.set(p["m"])
        self._on_type_changed()

        matrix = p["matrix"]
        for r in range(len(matrix)):
            for c in range(len(matrix[0])):
                self.entries[r][c].delete(0, tk.END)
                self.entries[r][c].insert(0, str(matrix[r][c]))

        self._run()

    # --- Core Computation and Drawing ---

    def _run(self):
        # Read matrix from grid
        rows = len(self.entries)
        cols = len(self.entries[0])
        M = np.zeros((rows, cols), dtype=float)
        for r in range(rows):
            for c in range(cols):
                val = self.entries[r][c].get().strip()
                try:
                    M[r, c] = float(val) if val else 0.0
                except ValueError:
                    messagebox.showerror("Error", f"Invalid numeric entry at row {r+1}, col {c+1}")
                    return

        mtype = self.matrix_type.get()
        n = rows

        try:
            if mtype == "adjacency":
                if rows != cols:
                    raise ValueError("Adjacency matrix must be square (n x n).")
                G, edge_list = adj_to_graph(M)
                adj = M
            else:
                G, edge_list, adj = incidence_to_graph(M)

            node_labels = {i: VERTEX_LABELS[i] for i in range(n)}

            self._draw_graph(G, node_labels, edge_list)
            self._compute_and_draw_fcm(G, edge_list)
            self._compute_and_draw_csm(G, edge_list)
            self._fill_info(G, node_labels, edge_list, adj)

            self.status_var.set(f"Done: {G.number_of_nodes()} vertices, {len(edge_list)} edges analyzed.")
        except Exception as ex:
            messagebox.showerror("Execution Error", str(ex))
            self.status_var.set(f"Error: {ex}")

    def _draw_graph(self, G: nx.Graph, labels: dict, edge_list: list):
        self.fig_graph.clf()
        ax = self.fig_graph.add_subplot(111)
        ax.set_facecolor("#181825")

        pos = nx.spring_layout(G, seed=42)

        # Find spanning tree edges
        if G.number_of_nodes() > 0 and nx.is_connected(G):
            T = nx.minimum_spanning_tree(G)
            tree_set = {tuple(sorted((u, v))) for u, v in T.edges()}
            tree_edges = [e[:2] for e in edge_list if tuple(sorted(e[:2])) in tree_set]
            chord_edges = [e[:2] for e in edge_list if tuple(sorted(e[:2])) not in tree_set]
        else:
            tree_edges = [e[:2] for e in edge_list]
            chord_edges = []

        # Draw edges
        nx.draw_networkx_edges(G, pos, edgelist=tree_edges, ax=ax,
                               edge_color="#89b4fa", width=2.5, alpha=0.9)
        if chord_edges:
            nx.draw_networkx_edges(G, pos, edgelist=chord_edges, ax=ax,
                                   edge_color="#f38ba8", width=2.2, style="dashed", alpha=0.9)

        # Draw nodes
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color="#a6e3a1",
                               node_size=650, edgecolors="#1e1e2e", linewidths=2)
        nx.draw_networkx_labels(G, pos, labels=labels, ax=ax,
                                font_color="#1e1e2e", font_size=11, font_weight="bold")

        # Edge labels
        edge_labels_dict = {(u, v): lbl for u, v, lbl in edge_list}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels_dict, ax=ax,
                                     font_color="#f9e2af", font_size=8,
                                     bbox=dict(boxstyle="round,pad=0.2", facecolor="#181825", edgecolor="none"))

        # Legend
        patches = [
            mpatches.Patch(color="#89b4fa", label="Tree Branch (Spanning Tree)"),
            mpatches.Patch(color="#f38ba8", label="Chord (Non-Tree Edge)"),
        ]
        ax.legend(handles=patches, loc="upper right", fontsize=8,
                  facecolor="#313244", edgecolor="#45475a", labelcolor="#cdd6f4")

        ax.set_title("Graph Visualization", color="#cdd6f4", fontsize=12, fontweight="bold", pad=8)
        ax.axis("off")
        self.fig_graph.tight_layout()
        self.canvas_graph.draw()

    def _draw_matrix_heatmap(self, fig, canvas, mat: np.ndarray, row_labels: list, col_labels: list, title: str, cmap="YlOrRd"):
        fig.clf()
        ax = fig.add_subplot(111)
        ax.set_facecolor("#181825")

        if mat.size == 0:
            ax.text(0.5, 0.5, "No cycles / cuts available", ha="center", va="center", color="#f38ba8")
            ax.axis("off")
            canvas.draw()
            return

        im = ax.imshow(mat, cmap=cmap, aspect="auto", vmin=0, vmax=1)
        rows, cols = mat.shape

        for r in range(rows):
            for c in range(cols):
                val = mat[r, c]
                color = "white" if val > 0.5 else "#cdd6f4"
                ax.text(c, r, str(int(val)), ha="center", va="center", fontsize=9, color=color, fontfamily="Consolas")

        ax.set_xticks(range(cols))
        ax.set_yticks(range(rows))
        ax.set_xticklabels(col_labels, fontsize=8, color="#cdd6f4", fontfamily="Consolas")
        ax.set_yticklabels(row_labels, fontsize=8, color="#cdd6f4", fontfamily="Consolas")
        ax.tick_params(colors="#585b70")
        for spine in ax.spines.values():
            spine.set_edgecolor("#45475a")

        ax.set_title(title, color="#cdd6f4", fontsize=11, fontweight="bold", pad=8)
        fig.tight_layout()
        canvas.draw()

    def _compute_and_draw_fcm(self, G: nx.Graph, edge_list: list):
        B, cycle_labels, col_labels, tree_edges, chord_edges = compute_fundamental_cycle_matrix(G, edge_list)
        self._draw_matrix_heatmap(self.fig_fcm, self.canvas_fcm, B, cycle_labels, col_labels,
                                  "Fundamental Cycle Matrix: B_f = [ I_mu | B_t ]", cmap="YlOrRd")

        # Text output
        self.fcm_text.delete("1.0", tk.END)
        self.fcm_text.insert(tk.END, f"Cyclomatic number (mu) = {len(chord_edges)}\n")
        self.fcm_text.insert(tk.END, f"Tree Branches : {', '.join([e[2] for e in tree_edges])}\n")
        self.fcm_text.insert(tk.END, f"Chords        : {', '.join([e[2] for e in chord_edges])}\n\n")
        self.fcm_text.insert(tk.END, "Fundamental Cycles:\n")
        for c in cycle_labels:
            self.fcm_text.insert(tk.END, f"  • {c}\n")

    def _compute_and_draw_csm(self, G: nx.Graph, edge_list: list):
        Q, cut_labels, col_labels = compute_cutset_matrix(G, edge_list)
        self._draw_matrix_heatmap(self.fig_csm, self.canvas_csm, Q, cut_labels, col_labels,
                                  "Fundamental Cut-Set Matrix: Q = [ C_c | I ]", cmap="PuBu")

        # Text output
        self.csm_text.delete("1.0", tk.END)
        self.csm_text.insert(tk.END, f"Fundamental Cut-Sets (rank = {len(cut_labels)}):\n")
        for s in cut_labels:
            self.csm_text.insert(tk.END, f"  • {s}\n")

    def _fill_info(self, G: nx.Graph, labels: dict, edge_list: list, adj: np.ndarray):
        self.info_text.configure(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)

        out = []
        out.append("=" * 60)
        out.append("  GRAPH PROPERTIES")
        out.append("=" * 60)
        out.append(f"  Vertices (n) : {G.number_of_nodes()}")
        out.append(f"  Edges    (m) : {len(edge_list)}")
        out.append(f"  Connected    : {'Yes' if nx.is_connected(G) else 'No'}")
        if G.number_of_nodes() > 0:
            mu = len(edge_list) - G.number_of_nodes() + nx.number_connected_components(G)
            out.append(f"  Cyclomatic # : {mu} (number of fundamental cycles)")

        out.append("\n-- Degrees --")
        for node in sorted(G.nodes()):
            out.append(f"  Node {labels.get(node, str(node))}: degree {G.degree(node)}")

        out.append("\n-- Adjacency Matrix A --")
        n = adj.shape[0]
        header = "    " + " ".join(f"{labels.get(c, str(c)):>3}" for c in range(n))
        out.append(header)
        for r in range(n):
            row_str = f"{labels.get(r, str(r)):>3} " + " ".join(f"{int(adj[r, c]):>3}" for c in range(n))
            out.append(row_str)

        out.append("\n-- Edge List --")
        for u, v, lbl in edge_list:
            out.append(f"  {lbl}: ({labels.get(u, u)} - {labels.get(v, v)})")

        out.append("\n-- Critical Links (Bridges) --")
        if nx.is_connected(G):
            bridges = list(nx.bridges(G))
            if bridges:
                for u, v in bridges:
                    out.append(f"  {labels.get(u, u)} - {labels.get(v, v)} is a bridge!")
            else:
                out.append("  None (graph has no bridges, edge connectivity >= 2)")
        else:
            out.append("  Graph is disconnected")

        out.append("=" * 60)
        self.info_text.insert(tk.END, "\n".join(out))
        self.info_text.configure(state=tk.DISABLED)


if __name__ == "__main__":
    app = GraphVisualizerApp()
    app.mainloop()

