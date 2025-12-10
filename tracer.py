import json

DEFAULT_CONFIG = {
    "left": "left",
    "right": "right",
    "parent": "parent",
    "key": "key",
    "root": "root"
}


class Tracer:
    def __init__(self, config=DEFAULT_CONFIG):
        self.history = []
        self.observed_tree = None # We will attach the real tree here later
        self.config = config # Configuration for attribute names
        self.locking = False # To prevent recursive logging (if True meaning we take a snapshot else )
        self.registered_nodes = {} # To track nodes we've seen (important for detecting)
        
    def set_tree(self, tree):
        self.observed_tree = tree

    def log(self, active_node_key, action):
        # Snapshot the tree structure at this moment
        if self.locking:
            return
        
        self.locking = True  # Prevent recursive logging
        snapshot = None
        if self.observed_tree is not None:
            root_node = getattr(self.observed_tree, self.config["root"])
            if root_node is not None:
                snapshot = serialize_forest(root_node, self.config, self.registered_nodes)
                
        self.locking = False  # Release the lock

        # Log the action with the current snapshot
        print(f"[LOG] Node {active_node_key}: {action}")
        self.history.append({
            "node": active_node_key,
            "action": action,
            "snapshot": snapshot
        })
    
    def add_registered_node(self, real_node):
        if hasattr(real_node, "_real_node"):
            print(f"⚠️ WARNING: SpyNode detected inside SpyNode! ID: {id(real_node)}")
        if id(real_node) not in self.registered_nodes and real_node is not None:
            self.registered_nodes[id(real_node)] = real_node
        
        
# --- 1. SERIALIZER (Robust "Visited Set" Approach) ---
def serialize_forest(root_node, config, registered_nodes_dict):
    subtrees = []
    
    # Track IDs we have successfully serialized
    visited_ids = set()

    # 1. Serialize Main Tree (Always try to serialize root, even if not registered)
    if root_node is not None:
        main_tree = serialize_tree(root_node, config, visited_ids)
        if main_tree:
            subtrees.append(main_tree)

    
    
    # 2. Serialize Floating Nodes
    # Only process nodes that are registered BUT were not found in the main tree
    for node_id, node in list(registered_nodes_dict.items()):
        # If we haven't visited this node yet, it's a floating tree
        if id(node) not in visited_ids:
            floating_tree = serialize_tree(node, config, visited_ids)
            if floating_tree:
                subtrees.append(floating_tree)
    

    return subtrees

def serialize_tree(node, config, visited_ids, parent_id=None):
    if node is None:
        return None

    node_id = id(node)
    
    # CYCLE DETECTION: If we've already serialized this node in this snapshot, stop.
    if node_id in visited_ids:
        return None
    
    # Mark as visited
    visited_ids.add(node_id)
    
    try:
        key = getattr(node, config["key"])
    except AttributeError:
        key = "???"

    node_left = getattr(node, config["left"], None)
    node_right = getattr(node, config["right"], None)
    
    return {
        "id": node_id, # This is an INT, the JS fix above handles it.
        "name": str(key),
        "children": [
            serialize_tree(node_left, config, visited_ids, node_id),
            serialize_tree(node_right, config, visited_ids, node_id)
        ],
        "parent": parent_id
    }
        
class SpyNode:
    def __init__(self, real_node, tracer, config=DEFAULT_CONFIG):
        # We use object.__setattr__ to avoid triggering our own trap!
        
        # save check to avoid nested SpyNodes IMORTANRT!!!!
        while hasattr(real_node, "_real_node"):
            real_node = real_node._real_node
        super().__setattr__("_real_node", real_node)
        super().__setattr__("_tracer", tracer)
        super().__setattr__("_config", config)
        tracer.add_registered_node(real_node)
        
    # HELPER: Generate the same ID format as the serializer
    def _get_id(self, node):
        # Handle None keys for sentinel nodes
        return id(node)

    # 1. TRAP READS (e.g., "current = current.left")
    def __getattribute__(self, name):
        # 1. ALLOW INTERNAL METHODS/ATTRIBUTES
        if name in ["_real_node", "_tracer", "_config", "_get_id"]:
             return super().__getattribute__(name)
        
        # If the code asks for _get_id, give it the Spy's method, don't pass to real node!
        if name in ["_real_node", "_tracer", "_config", "_get_id"]:
             return super().__getattribute__(name)
        
        # Get internal helpers
        real_node = super().__getattribute__("_real_node")
        tracer = super().__getattribute__("_tracer")
        config = super().__getattribute__("_config")

        # Logic: If the user asks for "left" or "right", they are traversing!
        if name in [config["left"], config["right"], config["parent"]]:
            
            # Use the NEW ID format for logging
            active_id = self._get_id(real_node)
            
            # Get the real child
            child_node = getattr(real_node, name)
            
            # Log the traversal action
            if name in [config["left"], config["right"]]:
                tracer.log(active_id, f"lokking at {name} child {getattr(child_node, config['key'], 'None') if child_node else 'None'}")
            else:
                tracer.log(active_id, f"lokking at parent")
            
            
            # CRITICAL: If the child exists, wrap IT in a Spy too!
            # This ensures the spy follows the user down the tree.
            if child_node is not None:
                return SpyNode(child_node, tracer, config)
            else:
                return None
            
        if name == config["key"]:
            # Get the key of the current node for logging
            active_id = self._get_id(real_node)
            key = getattr(real_node, name)
            tracer.log(active_id, f"Accessing key {key}")
            return getattr(real_node, name)
        
        # If they ask for any other attribute, just give it to them
        return getattr(real_node, name)

    # 2. TRAP WRITES (e.g., "current.left = Node(5)")
    def __setattr__(self, name, value):
        # 1. Handle Internal Attributes (Safe init)
        if name in ["_real_node", "_tracer", "_config"]:
             return super().__setattr__(name, value)
         
        real_node = super().__getattribute__("_real_node")
        tracer = super().__getattribute__("_tracer")
        config = super().__getattribute__("_config")

        actual_value = value
        if isinstance(value, SpyNode):
            actual_value = value._real_node
        
        if name in [config["left"], config["right"], config["parent"]]:
            
            # Perform the actual write on the real node
            setattr(real_node, name, actual_value)
            
            # Use the NEW ID format for logging
            active_id = self._get_id(real_node)
            
            val_str = "None"
            if actual_value is not None:
                # Be careful: value might be a SpyNode or a RealNode
                # We need to access its key safely
                val_key = getattr(actual_value, config["key"], "???")
                val_str = str(val_key)
            
            # Log the insertion action
            tracer.log(active_id, f"Inserted node {val_str} at {name}")
        else:
            # Allow setting other attributes normally
            object.__setattr__(real_node, name, actual_value)
            
            
class spy_BinaryTree:
    def __init__(self, real_tree, tracer, config = DEFAULT_CONFIG):
        # Initialize internal attributes safely
        super().__setattr__("_real_tree", real_tree)
        super().__setattr__("_tracer", tracer)
        super().__setattr__("_config", config)
        
    def __getattribute__(self, name):
        # 1. Access internal spy attributes safely
        if name in ["_real_tree", "_tracer", "_config"]:
            return super().__getattribute__(name)

        real_tree = super().__getattribute__("_real_tree")
        tracer = super().__getattribute__("_tracer")
        config = super().__getattribute__("_config")
        
        # 2. Trap the 'root' attribute
        # This is critical: When 'insert' calls 'self.root', it lands here.
        if name == config["root"]:
            root_node = getattr(real_tree, config["root"])
            if root_node is not None:
                # Wrap the root so traversal can be tracked from the very top
                return SpyNode(root_node, tracer, config)
            return None
            
        # 3. Handle Methods (The "Hijack")
        attr = getattr(real_tree, name)
        
        # If the attribute is a bound method (like 'insert'), we must re-bind it!
        if callable(attr) and hasattr(attr, "__self__"):
            # Get the unbound function from the class (e.g., BinaryTree.insert)
            func = getattr(type(real_tree), name)
            
            # Return a wrapper that calls the function with 'self' = THIS SPY
            # forcing the method to use our traps (like self.root or self.left)
            def method_proxy(*args, **kwargs):
                return func(self, *args, **kwargs)
            return method_proxy

        # If it's just a regular attribute (not a method), return it
        return attr

    def __setattr__(self, name, value):
        # 4. Trap Writes (e.g., self.root = Node(key))
        # If 'insert' sets self.root, we must apply that to the REAL tree.
        real_tree = super().__getattribute__("_real_tree")
        actual_value = value
        if isinstance(value, SpyNode):
            actual_value = value._real_node
        setattr(real_tree, name, actual_value)
        
        



# ==========================================         
# --- 1. The User's Logic (Standard Class) ---
class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None

class BinaryTree:
    def __init__(self):
        self.root = None

    def insert(self, key):
        if self.root is None:
            self.root = Node(key)
            return
        
        # This is a standard iterative insert (Could be recursive too, doesn't matter!)
        current = self.root
        while True:
            if key < current.key:
                if current.left is None:
                    current.left = Node(key)
                    break
                else:
                    current = current.left
            else:
                if current.right is None:
                    current.right = Node(key)
                    break
                else:
                    current = current.right
    
    def search(self, key):
        """Search for a key in the binary tree. Returns True if found, False otherwise."""
        current = self.root
        while current is not None:
            if key == current.key:
                return True
            elif key < current.key:
                current = current.left
            else:
                current = current.right
        return False
    
    
# ==========================================
# TEST: A "Weird" User Implementation
# ==========================================

# Imagine a user submits this code. 
# They use 'val', 'l', 'r', and 'head' instead of standard names.

class WeirdNode:
    def __init__(self, val):
        self.val = val   # Not 'key'
        self.l = None    # Not 'left'
        self.r = None    # Not 'right'

class WeirdTree:
    def __init__(self):
        self.head = None # Not 'root'

    def add_stuff(self, val):
        if self.head is None:
            self.head = WeirdNode(val)
            return
        
        curr = self.head
        while True:
            if val < curr.val:
                if curr.l is None:
                    curr.l = WeirdNode(val)
                    break
                else:
                    curr = curr.l
            else:
                if curr.r is None:
                    curr.r = WeirdNode(val)
                    break
                else:
                    curr = curr.r
    
    def find_stuff(self, val):
        """Recursive search for a value in the weird tree."""
        return self._find_recursive(self.head, val)
    
    def _find_recursive(self, node, val):
        """Helper method for recursive search."""
        # Base case: node is None
        if node is None:
            return False
        
        # Base case: found the value
        if val == node.val:
            return True
        
        # Recursive case: search left or right
        if val < node.val:
            return self._find_recursive(node.l, val)
        else:
            return self._find_recursive(node.r, val)
        
# --- EXECUTION ---

# 1. Define the Config for this specific user
user_config = {
    "left": "left",
    "right": "right",
    "parent": "parent",
    "key": "key",
    "root": "root"
}

from test_avl import AVLTree, AVLNode
# 2. Initialize Tracer
tracer = Tracer(config=user_config)
# 3. Wrap User's Tree with Spy
avl_tree = AVLTree()
spy_tree = spy_BinaryTree(avl_tree, tracer, config=user_config)
tracer.set_tree(avl_tree)
# 3. User Operations
spy_tree.insert(6, "a")
spy_tree.insert(7, "b")
spy_tree.insert(8, "c")
spy_tree.insert(9, "d")




# 4. Verify Output
print("\n--- JSON Output (Proof it worked) ---")
print(json.dumps(tracer.history[50], indent=2))

# 5. Export for Visualizer
with open("tree_data.js", "w") as f:
    f.write(f"const TREE_HISTORY = {json.dumps(tracer.history)};")

"""# --- EXECUTION: WeirdTree Test ---

# 1. Define the Config for the WeirdTree (custom attribute names)
weird_config = {
    "left": "l",      # WeirdNode uses 'l' not 'left'
    "right": "r",     # WeirdNode uses 'r' not 'right'
    "parent": "parent",  # WeirdNode doesn't have parent, but we can add it
    "key": "val",     # WeirdNode uses 'val' not 'key'
    "root": "head"    # WeirdTree uses 'head' not 'root'
}

# 2. Initialize Tracer with weird config
tracer_weird = Tracer(config=weird_config)

# 3. Create and wrap the WeirdTree
weird_tree = WeirdTree()
spy_weird_tree = spy_BinaryTree(weird_tree, tracer_weird, config=weird_config)
tracer_weird.set_tree(weird_tree)

# 4. User Operations (using the spy)
print("--- Inserting into WeirdTree ---")
spy_weird_tree.add_stuff(50)
spy_weird_tree.add_stuff(30)
spy_weird_tree.add_stuff(70)
spy_weird_tree.add_stuff(20)
spy_weird_tree.add_stuff(40)
spy_weird_tree.add_stuff(60)
spy_weird_tree.add_stuff(80)

print("\n--- Searching in WeirdTree ---")
result1 = spy_weird_tree.find_stuff(40)
print(f"Search for 40: {result1}")

result2 = spy_weird_tree.find_stuff(99)
print(f"Search for 99: {result2}")

# 5. Verify Output
print("\n--- Total Steps Logged ---")
print(f"Total history entries: {len(tracer_weird.history)}")

print("\n--- Sample Log Entry ---")
if len(tracer_weird.history) > 10:
    print(json.dumps(tracer_weird.history[10], indent=2))

# 6. Export for Visualizer
with open("tree_data.js", "w") as f:
    f.write(f"const TREE_HISTORY = {json.dumps(tracer_weird.history)};")
    print("\n✅ Exported to tree_data.js")"""
