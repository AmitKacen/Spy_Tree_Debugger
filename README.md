🕵️‍♂️ Spy Tree Debugger
A zero-config, transparent visualizer for Python binary tree algorithms.

[Insert a high-quality screenshot of your final D3/Vis.js visualization here] Above: An AVL tree rotation captured step-by-step by the Spy Debugger.

📖 Introduction
Standard debuggers show you the state of variables at a specific breakpoint. They are terrible at showing the history of how a data structure evolved over time.

Spy Tree Debugger solves this by recording every single read, write, traversal, and structural change in your binary tree algorithm.

The best part? It requires ZERO modifications to your algorithm's code.

You write standard Python node logic (e.g., an iterative insert, recursive search, or AVL rotation), and the "Spy" wraps your data structure, invisibly capturing the execution flow and exporting it into an interactive web-based playback.

🧠 How It Works Under the Hood (The "Infection" Mechanism)
This tool does not use "monkey patching" (modifying your classes globaly), nor does it rely on complex sys.settrace calls.

Instead, it uses the Transparent Proxy Pattern. We wrap your initial root node in a "SpyNode." This Spy acts as a "Man-in-the-Middle" for all interactions between your code and the actual data.

The Core Philosophy: "The Shadow Spy"
To ensure your complex algorithms (like AVL balancing logic) never break, we adhere to a strict rule: The physical tree structure in memory must remain "clean" (composed of raw Python objects), while the variables holding current execution position are "infected" (wrappers).

We achieve this through asymmetrical handling of Reads vs. Writes.

1. Trapping Reads ("The Infection")
When your code attempts to traverse the tree (e.g., accessing .left or .right), the Spy intercepts the request.

Instead of returning the raw child node, it instantly wraps that child in a new, ephemeral SpyNode and hands that wrapper to your code. Your algorithm thinks it's holding a regular node, but it's actually holding a tracking device.

קטע קוד

graph TD
    A[User Code: 'current.left'] -->|Calls __getattribute__| B(SpyNode Wrapper);
    B -->|Looks inside| C[Real Node in Tree];
    C -->|Finds Raw Child| D[Raw Child Node];
    D -->|WRAPS| E(New Ephermal SpyNode);
    E -->|Returns to User| F[User Variable 'current' holds Spy];
    style B fill:#ffcccc,stroke:#333,stroke-width:2px
    style E fill:#ffcccc,stroke:#333,stroke-width:2px
    style C fill:#e6f3ff,stroke:#333,stroke-width:2px
    style D fill:#e6f3ff,stroke:#333,stroke-width:2px
[Visual Diagram 1: How the Spy infects variables during traversal]

2. Trapping Writes ("The Cleaning")
When your code attempts to modify the structure (e.g., parent.left = new_child), the Spy intercepts this assignment.

Crucially, before saving the new value into the actual tree structure, the Spy unwraps it. It peels off any proxy layers to find the raw, underlying Python object. It then saves only the raw object into the tree's memory.

Why is this critical? Because the physical links (.left and .right) in memory remain pure Python objects, your algorithm's internal logic (like isinstance checks or complex rotation assignments) works exactly as intended without ever realizing it's being watched.

קטע קוד

graph LR
    A[User Variable holds Spy] -->|Assigns: 'parent.left = me'| B(SpyNode '__setattr__');
    B -- UNWRAPS VALUE --> C[Raw Python Object];
    C -->|Saves to| D[Real Memory Tree Structure];
    style A fill:#ffcccc,stroke:#333,stroke-width:2px
    style B fill:#ffcccc,stroke:#333,stroke-width:2px
    style D fill:#e6f3ff,stroke:#333,stroke-width:2px
[Visual Diagram 2: How the Spy ensures the tree structure remains clean on write]

The Visualization Pipeline
Trap: A SpyNode intercepts an action (e.g., "Traversing left").

Log: The action is recorded by the central Tracer.

Snapshot: The Tracer immediately serializes the current state of the entire real tree into JSON.

Export: The history of actions and snapshots is exported to a JavaScript file, ready for the frontend viewer.

🚀 Usage Example
You don't change your Node or Tree classes. You just wrap the instance before running your operations.

Before (Your Standard Code)
Python

# Your standard classes
class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        # self.parent = None (Optional, supported by visualizer)

tree = BinaryTree()
tree.insert(50)
tree.insert(30)
tree.insert(70)
After (With Spy Visualization)
Python

from spy_debugger import Tracer, spy_BinaryTree

# 1. Define your structure config (tell the spy your attribute names)
config = {"left": "left", "right": "right", "parent": "parent", "key": "key", "root": "root"}

# 2. Initialize the tracer
tracer = Tracer(config=config)

# 3. Instantiate your real tree
real_tree = BinaryTree()

# 4. Wrap it with the Spy!
spy_tree = spy_BinaryTree(real_tree, tracer, config=config)

# ---- Run your operations on the SPY tree ----
# Every step is now recorded.
spy_tree.insert(50)
spy_tree.insert(30)
spy_tree.insert(70)
# ---------------------------------------------

# 5. Export the data for the viewer
tracer.export_to_js("tree_data.js")
print("Visualization data exported!")
⚙️ Technical Highlights
Duck Typing over isinstance: To ensure robustness against code reloading in interactive environments (like Jupyter), the unwrapping mechanism uses attribute detection (hasattr(obj, '_spy_debug_wrapped_node')) rather than strict type checking.

Equality Delegation: The SpyNode overrides __eq__ and __hash__ to delegate back to the real node. To your algorithm, spy_wrapper == real_node evaluates to True, ensuring lookups and comparisons work as expected.

Cycle Detection Serializer: The snapshot mechanism can handle complex graphs, including parent pointers and cycles, without entering infinite loops.
