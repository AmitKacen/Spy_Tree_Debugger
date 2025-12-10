import networkx as nx
import matplotlib.pyplot as plt

def hierarchy_pos(G, root=None, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5):
    """
    (Standard Python snippet to position nodes in a tree shape)
    G: the graph (networkx object)
    root: the root node of the current branch
    """
    if not nx.is_tree(G):
        raise TypeError('cannot use hierarchy_pos on a graph that is not a tree')

    def _hierarchy_pos(G, root, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5, pos = None, parent = None):
        if pos is None:
            pos = {root:(xcenter,vert_loc)}
        else:
            pos[root] = (xcenter, vert_loc)
        children = list(G.neighbors(root))
        if not isinstance(G, nx.DiGraph) and parent is not None:
            children.remove(parent)  
        if len(children)!=0:
            dx = width/len(children) 
            nextx = xcenter - width/2 - dx/2
            for child in children:
                nextx += dx
                pos = _hierarchy_pos(G,child, width=dx, vert_gap=vert_gap, 
                                    vert_loc=vert_loc-vert_gap, xcenter=nextx,
                                    pos=pos, parent=root)
        return pos

    return _hierarchy_pos(G, root, width, vert_gap, vert_loc, xcenter)


def visualize_step(snapshot, step_number, total_steps):
    tree_data = snapshot["tree_structure"]
    active_node = snapshot["active_node_key"]
    message = snapshot["message"]
    
    # 1. Create the Graph Object
    G = nx.Graph()
    
    # 2. Recursively build the graph from our dictionary
    def build_graph(node_dict):
        if not node_dict:
            return
        key = node_dict["key"]
        G.add_node(key)
        
        if node_dict["left"]:
            G.add_edge(key, node_dict["left"]["key"])
            build_graph(node_dict["left"])
            
        if node_dict["right"]:
            G.add_edge(key, node_dict["right"]["key"])
            build_graph(node_dict["right"])
            
    if tree_data:
        build_graph(tree_data)
        root_key = tree_data["key"]
        pos = hierarchy_pos(G, root=root_key)
    else:
        # Empty tree case
        G.add_node("Empty")
        pos = {"Empty": (0.5, 0)}

    # 3. Setup the Colors (The "Debugger" Logic)
    # Default color for all nodes is Blue
    color_map = []
    for node in G:
        if node == active_node:
            color_map.append('red')   # HIGHLIGHT the active node in RED
        else:
            color_map.append('skyblue')

    # 4. Draw the Graph
    plt.figure(figsize=(8, 6))
    plt.title(f"Step {step_number}/{total_steps}: {message}", fontsize=12)
    
    nx.draw(G, pos, node_color=color_map, with_labels=True, 
            node_size=2000, font_size=15, font_weight="bold", arrows=False)
    
    plt.show() # <--- This pauses the code until you close the window
    
    
# --- 1. Run the Logic ---
tree = BinaryTree()
print("Running Tree Operations...")
tree.insert(50)
tree.insert(30)
tree.insert(20)
tree.insert(40)
tree.insert(70)

# --- 2. Play the Movie ---
print(f"Captured {len(tree.history)} steps. Starting Replay...")

for i, snapshot in enumerate(tree.history):
    # Visualize each step one by one
    visualize_step(snapshot, i + 1, len(tree.history))