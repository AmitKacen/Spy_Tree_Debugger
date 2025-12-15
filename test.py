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
    
    def delete(self, key):
        """Delete a node with the given key from the binary tree."""
        parent = None
        current = self.root
        
        # Find the node to delete
        while current is not None and current.key != key:
            parent = current
            if key < current.key:
                current = current.left
            else:
                current = current.right
        
        # Key not found
        if current is None:
            return False
        
        # Case 1: Node has no children (leaf)
        if current.left is None and current.right is None:
            if current == self.root:
                self.root = None
            elif parent.left == current:
                parent.left = None
            else:
                parent.right = None
        
        # Case 2: Node has one child
        elif current.left is None or current.right is None:
            child = current.left if current.left else current.right
            if current == self.root:
                self.root = child
            elif parent.left == current:
                parent.left = child
            else:
                parent.right = child
        
        # Case 3: Node has two children
        else:
            # Find the in-order successor (smallest in right subtree)
            succ_parent = current
            successor = current.right
            while successor.left is not None:
                succ_parent = successor
                successor = successor.left
            
            # Replace current's key with successor's key
            current.key = successor.key
            
            # Delete the successor (it has at most one child - right)
            if succ_parent.left == successor:
                succ_parent.left = successor.right
            else:
                succ_parent.right = successor.right
        
        return True
    
    
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