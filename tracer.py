import json

DEFAULT_CONFIG = {
    "left": "left",
    "right": "right",
    "parent": "parent",
    "key": "key",
    "root": "root"
}

# --- 1. GLOBAL HELPERS ---
def safe_unwrap(value):
    """Recursively strips off Spy wrappers."""
    while hasattr(value, "_real_node"):
        value = value._real_node
    return value


class Tracer:
    def __init__(self, config=DEFAULT_CONFIG):
        self.history = []
        self.observed_tree = None # We will attach the real tree here later
        self.config = config # Configuration for attribute names
        self.locking = False # To prevent recursive logging (if True meaning we take a snapshot else )
        self.registered_nodes = {} # To track nodes we've seen (important for detecting)
        self.method = None # Current method being traced
        
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
            "snapshot": snapshot,
            "method": self.method
        })
    
    def add_registered_node(self, real_node):
        if id(real_node) not in self.registered_nodes and real_node is not None:
            self.registered_nodes[id(real_node)] = real_node
    
    def update_cuurrent_method(self, method_name):
        self.method = method_name
        self.log("N/A", f"Entering method {method_name}")
        
        
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

def serialize_tree(node, config, visited_ids):
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
    ## TODO: unwarp proxies from children?
    node_left = getattr(node, config["left"], None)
    node_right = getattr(node, config["right"], None)
    
    node_parent = getattr(node, config["parent"], None)
    parent_id=None
    if node_parent is not None:
        node_parent = safe_unwrap(node_parent)
        parent_id = id(node_parent)
    
    # Collect all attributes of the node (excluding left, right, parent, key which we handle separately)
    skip_attrs = {config["left"], config["right"], config["parent"], config["key"], "__dict__", "__class__", "__module__", "__weakref__", "__doc__"}
    attributes = {}
    for attr_name in dir(node):
        # Skip private/magic attributes and the ones we already handle
        if attr_name.startswith("_") or attr_name in skip_attrs:
            continue
        try:
            attr_value = getattr(node, attr_name)
            # Skip methods/callables
            if callable(attr_value):
                continue
            # Handle basic types
            if isinstance(attr_value, (int, float, str, bool, type(None))):
                attributes[attr_name] = attr_value
            else:
                # For complex objects, just store their string representation
                attributes[attr_name] = str(attr_value)
        except Exception:
            pass  # Skip attributes that can't be accessed
    
    return {
        "id": node_id, # This is an INT, the JS fix above handles it.
        "name": str(key),
        "children": [
            serialize_tree(node_left, config, visited_ids),
            serialize_tree(node_right, config, visited_ids)
        ],
        "parent": parent_id,
        "attributes": attributes
    }
        
class ProxyNode:
    def __init__(self, real_node, tracer, config=DEFAULT_CONFIG):
        # save check to avoid nested SpyNodes IMORTANRT!!!!
        real_node = safe_unwrap(real_node)
        
        # We use object.__setattr__ to avoid triggering our own trap!
        super().__setattr__("_real_node", real_node)
        super().__setattr__("_tracer", tracer)
        super().__setattr__("_config", config)
        tracer.add_registered_node(real_node)
    
    # COMPARISON: Compare the real nodes, not the wrappers!
    def __eq__(self, other):
        # Get real node from self
        self_real = super().__getattribute__("_real_node")
        
        # Handle None comparison
        if other is None:
            return self_real is None
        
        # Get real node from other (if it's a ProxyNode)
        other_real = safe_unwrap(other)
        
        return self_real is other_real

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self):
        real_node = safe_unwrap(super().__getattribute__("_real_node"))
        return hash(id(real_node))
    
    def __bool__(self):
        real_node = safe_unwrap(super().__getattribute__("_real_node"))
        return real_node is not None
    
    # < (Less Than)
    def __lt__(self, other):
        return self._real_node < safe_unwrap(other)

    # <= (Less Than or Equal)
    def __le__(self, other):
        return self._real_node <= safe_unwrap(other)

    # > (Greater Than)
    def __gt__(self, other):
        return self._real_node > safe_unwrap(other)

    # >= (Greater Than or Equal)
    def __ge__(self, other):
        return self._real_node >= safe_unwrap(other)
        
    # HELPER: Generate the same ID format as the serializer
    def _get_id(self, node):
        return id(node)

    # 1. TRAP READS (e.g., "current = current.left")
    def __getattribute__(self, name):
        # 1. ALLOW INTERNAL METHODS/ATTRIBUTES
        if name in ["_real_node", "_tracer", "_config", "_get_id"]:
             return super().__getattribute__(name)
        
        # Get internal helpers
        real_node = super().__getattribute__("_real_node")
        real_node = safe_unwrap(real_node)
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
                tracer.log(active_id, f"looking at {name} child {getattr(child_node, config['key'], 'None') if child_node else 'None'}")
            else:
                tracer.log(active_id, f"looking at parent {getattr(child_node, config['key'], 'None') if child_node else 'None'}")
            
            
            # CRITICAL: If the child exists, wrap IT in a Spy too!
            # This ensures the spy follows the user down the tree.
            if child_node is not None:
                if hasattr(child_node, "_real_node"):
                    return child_node
                return ProxyNode(child_node, tracer, config)
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
        
        # Use the NEW ID format for logging
        active_id = self._get_id(real_node)
            
        actual_value = value
        if isinstance(value, ProxyNode):
            actual_value = value._real_node

        
        if name in [config["left"], config["right"], config["parent"]]:
            
            # Perform the actual write on the real nod
            setattr(real_node, name, actual_value)
            
            
            
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
            tracer.log(active_id, f"Updating attribute {name} to {actual_value}")
            object.__setattr__(real_node, name, actual_value)
            
            
class ProxyTree:
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
        if name in [config["root"], config["max"], config["min"]]:
            root_node = getattr(real_tree, name)
            if root_node is not None:
                if isinstance(root_node, ProxyNode):
                    return root_node
                return ProxyNode(root_node, tracer, config)
            return None
            
        # 3. Handle Methods (The "Hijack")
        attr = getattr(real_tree, name)
        
        # If the attribute is a bound method (like 'insert'), we must re-bind it!
        if callable(attr) and hasattr(attr, "__self__"):
            # Get the unbound function from the class (e.g., BinaryTree.insert)
            func = getattr(type(real_tree), name)
            self._tracer.update_cuurrent_method(name)
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
        actual_value = safe_unwrap(value)
        setattr(real_tree, name, actual_value)
        
        

# 1. Define the Config for this specific user
user_config = {
    "left": "left",
    "right": "right",
    "parent": "parent",
    "key": "key",
    "root": "root", 
    "max": "max_node",
    "min": "min_node"
}

from test_avl import AVLTree, AVLNode
# 2. Initialize Tracer
tracer = Tracer(config=user_config)
# 3. Wrap User's Tree with Spy
avl_tree = AVLTree()
spy_tree = ProxyTree(avl_tree, tracer, config=user_config)
tracer.set_tree(avl_tree)
# 3. User Operations
spy_tree.insert(6, "a")
spy_tree.insert(7, "b")
spy_tree.insert(8, "c")
spy_tree.insert(5, "d")
spy_tree.insert(10, "d")
spy_tree.insert(11, "d")
spy_tree.insert(4, "d")
spy_tree.insert(3, "d")
spy_tree.insert(2, "d")
test_node = spy_tree.search(7)[0]
spy_tree.delete(test_node)
spy_tree.finger_insert(12, "e")





# 4. Verify Output
print("\n--- JSON Output (Proof it worked) ---")
print(json.dumps(tracer.history[-1], indent=2))

# 5. Export for Visualizer
with open("tree_data.js", "w") as f:
    f.write(f"const TREE_HISTORY = {json.dumps(tracer.history)};")



