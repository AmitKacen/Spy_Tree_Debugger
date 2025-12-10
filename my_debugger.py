class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None

class BinaryTree:
    def __init__(self):
        self.root = None
        self.history = []  # <--- NEW: The storage for our "movie"

    def log_step(self, current_node_key, message):
        """
        Takes a snapshot of the current situation.
        """
        snapshot = {
            "active_node_key": current_node_key, # The node currently being visited
            "message": message,                  # What is happening (e.g., "Going Left")
            "tree_structure": self.to_dict(self.root) # The FULL tree state
        }
        self.history.append(snapshot)

    def insert(self, key):
        if self.root is None:
            self.root = Node(key)
            self.log_step(key, f"Root was empty. Inserted {key}") # Log creation
        else:
            self._insert_recursive(self.root, key)

    def _insert_recursive(self, current_node, key):
        # 1. LOG: We just arrived at this node
        self.log_step(current_node.key, f"Visiting {current_node.key}, checking {key}")

        if key < current_node.key:
            if current_node.left is None:
                current_node.left = Node(key)
                # 2. LOG: We just changed the tree (inserted node)
                self.log_step(key, f"Inserted {key} to the LEFT of {current_node.key}")
            else:
                self._insert_recursive(current_node.left, key)
        else:
            if current_node.right is None:
                current_node.right = Node(key)
                # 2. LOG: We just changed the tree (inserted node)
                self.log_step(key, f"Inserted {key} to the RIGHT of {current_node.key}")
            else:
                self._insert_recursive(current_node.right, key)
                
    # Add this inside the BinaryTree class
    def print_tree(self, node=None, level=0, prefix="Root: "):
        if node is None:
            node = self.root
            
        print("  " * level + prefix + str(node.key))
        
        if node.left:
            self.print_tree(node.left, level + 1, "L--- ")
        if node.right:
            self.print_tree(node.right, level + 1, "R--- ")
            
            
    def to_dict(self, node):
        """
        Converts the current tree state into a dictionary (JSON-like structure).
        This creates a 'frozen' copy of the data.
        """
        if node is None:
            return None
        
        return {
            "key": node.key,
            "left": self.to_dict(node.left),
            "right": self.to_dict(node.right)
        }
            
import json

tree = BinaryTree()
tree.insert(10)
tree.insert(5)

# Print the "Movie" data in a readable format
print(json.dumps(tree.history, indent=2))


def snapshot(func):
    """
    Decorator to take a snapshot before and after the function call.
    Assumes the first argument to the function is 'self' (the BinaryTree instance).
    """
    def wrapper(self, *args, **kwargs):
        # Snapshot before the operation
        self.log_step(None, f"Before {func.__name__} with args {args}, {kwargs}")
        
        result = func(self, *args, **kwargs)
        
        # Snapshot after the operation
        self.log_step(None, f"After {func.__name__} with args {args}, {kwargs}")
        
        return result
    return wrapper