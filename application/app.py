import matplotlib.pyplot as plt
import matplotlib.animation as animation
import networkx as nx
import numpy as np

# 1. Matriks Adjacency
adj_matrix = np.array([
    [0, 1, 1, 0],
    [1, 0, 1, 1],
    [1, 1, 0, 1],
    [0, 1, 1, 0]
])

G = nx.from_numpy_array(adj_matrix)
pos = nx.spring_layout(G, seed=42) # Posisi node tetap

# 2. Ambil urutan langkah penjelajahan node & edge (pencarian BFS dari node 0)
visited_nodes = list(nx.bfs_tree(G, source=0).nodes())
traversed_edges = list(nx.bfs_edges(G, source=0))

fig, ax = plt.subplots(figsize=(6, 5))

def update(frame):
    ax.clear()
    
    # Node dan edge yang sudah dikunjungi sampai frame saat ini
    current_nodes = visited_nodes[:frame + 1]
    current_edges = traversed_edges[:frame]
    
    # Gambar seluruh graf dasar (abu-abu)
    nx.draw_networkx_nodes(G, pos, node_color='lightgray', node_size=800, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color='gray', width=1, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=12, font_weight='bold', ax=ax)
    
    # Sorot edge yang dilalui (merah)
    if current_edges:
        nx.draw_networkx_edges(G, pos, edgelist=current_edges, edge_color='red', width=3, ax=ax)
        
    # Sorot node yang sudah dikunjungi (hijau)
    nx.draw_networkx_nodes(G, pos, nodelist=current_nodes, node_color='springgreen', node_size=800, ax=ax)
    
    # Sorot node yang sedang aktif saat ini (kuning)
    active_node = visited_nodes[frame]
    nx.draw_networkx_nodes(G, pos, nodelist=[active_node], node_color='yellow', node_size=1000, ax=ax)
    
    ax.set_title(f"Penjelajahan Graf (Langkah {frame + 1}: Mengunjungi Node {active_node})")

# Buat animasi berpindah tiap 1.2 detik (interval=1200 ms)
ani = animation.FuncAnimation(
    fig, 
    update, 
    frames=len(visited_nodes), 
    interval=1200, 
    repeat=True
)

plt.show()
