# 🕵️‍♂️ Spy Tree Debugger

**A zero-config, transparent visualizer for Python binary tree algorithms.**

---

## 📖 Introduction

Standard debuggers show you the *state* of variables at a specific breakpoint. They are terrible at showing the *history* of how a data structure evolved over time.

**Spy Tree Debugger** solves this by recording every single read, write, traversal, and structural change in your binary tree algorithm.

**The best part? It requires ZERO modifications to your algorithm's code.**

You write standard Python node logic (e.g., an iterative insert, recursive search, or AVL rotation), and the "Spy" wraps your data structure, invisibly capturing the execution flow and exporting it into an interactive web-based playback.

---

## 🧠 How It Works Under the Hood (The "Infection" Mechanism)

This tool does not use "monkey patching" (modifying your classes globally), nor does it rely on complex `sys.settrace` calls.

Instead, it uses the **Transparent Proxy Pattern**. We wrap your initial root node in a "SpyNode." This Spy acts as a "Man-in-the-Middle" for all interactions between your code and the actual data.

### Visualizing the Process

![Spy Tree Debugger Infection Mechanism](spy_mechanism_diagram.png)

### The Core Philosophy: "The Shadow Spy"

To ensure your complex algorithms (like AVL balancing logic) never break, we adhere to a strict rule: **The physical tree structure in memory must remain "clean" (composed of raw Python objects), while the variables holding current execution position are "infected" (wrappers).**

We achieve this through asymmetrical handling of Reads vs. Writes.

#### 1. Trapping Reads ("The Infection")
When your code attempts to traverse the tree (e.g., accessing `.left` or `.right`), the Spy intercepts the request.

Instead of returning the raw child node, it instantly wraps that child in a *new*, ephemeral SpyNode and hands that wrapper to your code. Your algorithm thinks it's holding a regular node, but it's actually holding a tracking device.

#### 2. Trapping Writes ("The Cleaning")
When your code attempts to modify the structure (e.g., `parent.left = new_child`), the Spy intercepts this assignment.

Crucially, before saving the new value into the actual tree structure, the Spy **unwraps** it. It peels off any proxy layers to find the raw, underlying Python object. It then saves *only* the raw object into the tree's memory.

**Why is this critical?**
Because the physical links (`.left` and `.right`) in memory remain pure Python objects, your algorithm's internal logic (like `isinstance` checks or complex rotation assignments) works exactly as intended without ever realizing it's being watched.

### The Visualization Pipeline

1.  **Trap:** A SpyNode intercepts an action (e.g., "Traversing left").
2.  **Log:** The action is recorded by the central Tracer.
3.  **Snapshot:** The Tracer immediately serializes the current state of the *entire real tree* into JSON.
4.  **Export:** The history of actions and snapshots is exported to a JavaScript file, ready for the frontend viewer.

---

## 🚀 Usage Example

You don't change your `Node` or `Tree` classes. You just wrap the instance before running your operations.

### Before (Your Standard Code)

```python
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
```

## After (With Spy Visualization)

```python
from spy_debugger import Tracer, ProxyTree

# 1. Define your structure config (tell the spy your attribute names)
config = {"left": "left", "right": "right", "parent": "parent", "key": "key", "root": "root"}

# 2. Initialize the tracer
tracer = Tracer(config=config)

# 3. Instantiate your real tree
real_tree = BinaryTree()

# 4. Wrap it with the Spy!
spy_tree = ProxyTree(real_tree, tracer, config=config)

# ---- Run your operations on the SPY tree ----
# Every step is now recorded.
spy_tree.insert(50)
spy_tree.insert(30)
spy_tree.insert(70)
# ---------------------------------------------

# 5. Export the data for the viewer
with open("tree_data.js", "w") as f:
    f.write(f"const TREE_HISTORY = {json.dumps(tracer.history)};")
