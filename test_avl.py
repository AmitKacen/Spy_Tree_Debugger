#id1:
#name1:
#username1:
#id2:
#name2:
#username2:


"""A class represnting a node in an AVL tree"""

class AVLNode(object):
	"""Constructor, you are allowed to add more fields. 
	
	@type key: int
	@param key: key of your node
	@type value: string
	@param value: data of your node
	"""
	def __init__(self, key, value):
		self.key = key
		self.value = value
		self.left = None
		self.right = None
		self.parent = None
		self.height = -1
		

	"""returns whether self is not a virtual node 

	@rtype: bool
	@returns: False if self is a virtual node, True otherwise.
	"""
	def is_real_node(self):
		if self is None:
			return False
		return self.key is not None


"""
A class implementing an AVL tree.
"""

class AVLTree(object):

	"""
	Constructor, you are allowed to add more fields.
	"""
	def __init__(self):
		self.root = None
		self.max_node = None
		self.size_count = 0


	"""searches for a node in the dictionary corresponding to the key (starting at the root)
        
	@type key: int
	@param key: a key to be searched
	@rtype: (AVLNode,int)
	@returns: a tuple (x,e) where x is the node corresponding to key (or None if not found),
	and e is the number of edges on the path between the starting node and ending node+1.
	"""
	def search(self, key):
		if self.root is None:
			return None, -1
		return self.rec_search(self.root, key, e=1)
		
	def rec_search(self,node, key, e):

		if node is None: # check if modifying for is_real_node is needed
			return None, e
		if key == node.key:
			return node, e
		
		e += 1
		if key < node.key:
			return self.rec_search(node.left, key, e)
		else:
			return self.rec_search(node.right, key, e)
		


	"""searches for a node in the dictionary corresponding to the key, starting at the max
        
	@type key: int
	@param key: a key to be searched
	@rtype: (AVLNode,int)
	@returns: a tuple (x,e) where x is the node corresponding to key (or None if not found),
	and e is the number of edges on the path between the starting node and ending node+1.
	"""
	def finger_search(self, key):

		if self.root is None:
			return None, -1
		
		e = 1
		curr = self.max_node
		while curr.parent.key >= key and curr.parent is not None:
			curr = curr.parent
			e += 1

		# now curr is the lowest ancestor of max_node with key less than or equal to key
		return self.rec_search(curr, key, e)
		


	"""inserts a new node into the dictionary with corresponding key and value (starting at the root)

	@type key: int
	@pre: key currently does not appear in the dictionary
	@param key: key of item that is to be inserted to self
	@type val: string
	@param val: the value of the item
	@rtype: (AVLNode,int,int)
	@returns: a 3-tuple (x,e,h) where x is the new node,
	e is the number of edges on the path between the starting node and new node before rebalancing,
	and h is the number of PROMOTE cases during the AVL rebalancing
	"""
	def insert(self, key, val):
		self.size_count += 1
		# Empty tree case
		if self.root is None:
			self.root = AVLNode(key, val)
			self.root.left = AVLNode(None, None)
			self.root.right = AVLNode(None, None)
			self.root.height = 0
			self.max_node = self.root
			return self.root, 0, 0
		e = 0  
		curr = self.root
		return self.insert_helper(curr, key, val, e)
		
	def insert_helper(self, curr, key, val, e):
		y = None

        # Traverse the tree to find the correct position for the new key
		while curr is not None and curr.is_real_node():
			y = curr
			if key < curr.key:
				curr = curr.left
			else:
				curr = curr.right
			e+= 1 # Increment edge count for each step down the tree

		# Create the new node, set its children to virtual nodes
		node = AVLNode(key, val)
		node.left = AVLNode(None, None)
		node.right = AVLNode(None, None)
		node.parent = y
		node.height = 0

		# Update max_node if necessary
		if self.max_node is None or key > self.max_node.key:
			self.max_node = node

		# Insert the new node into the tree
		if y == None:
			self.root = node
		elif node.key < y.key:
			y.left = node
		else:
			y.right = node
		e+= 1 # Count the edge to the new node
  
		# Rebalance the tree and count the number of rotations
		h = 0
		while y != None:
			BF = y.left.height - y.right.height

			# Check if node is balanced
			if abs(BF) < 2:
				# if the height is unchanged, no further rebalancing is needed
				if y.height == 1 + max(y.left.height, y.right.height):
					return node, e, h
				else:
					# Update height and move up the tree
					y.height = 1 + max(y.left.height, y.right.height)
					y = y.parent
					h+= 1   # Count height update as promote
			else:
				# Rebalance the tree
				self.rotation(y, BF)
				h+=1  # Count rebalancing as height update
				return node, e, h

	
	
	def rotation(self, node, BF):
		
		if BF == 2:
			child = node.left
			BF_check = child.left.height - child.right.height
			if BF_check >= 0:
				self.right_rotation(node)
			else:
				self.left_rotation(node.left)
				self.right_rotation(node)
		else:
			child = node.right
			BF_check = child.left.height - child.right.height
			if BF_check <= 0:
				self.left_rotation(node)
			else:
				self.right_rotation(node.right)
				self.left_rotation(node)
    
		return None # node ()


	def right_rotation(self, B):
			# performs right rotation on a given node
			A = B.left
			B.left = A.right

			if A.right.is_real_node():
				B.left.parent = B

			A.right = B
			A.parent = B.parent

			if A.parent != None:
				if  B.parent.left == B:
					A.parent.left = A
				else:
					A.parent.right = A
			else:
				self.root = A

			B.parent = A

			# Update height
			B.height = 1 + max(B.left.height, B.right.height)
			A.height = 1 + max(A.left.height, A.right.height)

			return    # child node, check if neccessary	

		
	def left_rotation(self, B):
			# performs left rotation on a given node
			A = B.right
			B.right = A.left

			if A.left.is_real_node():
				B.right.parent = B

			A.left = B
			A.parent = B.parent

			if B.parent != None:
				if B.parent.left == B:
					A.parent.left = A
				else:
					A.parent.right = A
			else:
				self.root = A

			B.parent = A

			# Update height
			B.height = 1 + max(B.left.height, B.right.height)
			A.height = 1 + max(A.left.height, A.right.height)

			return    # child node, check if neccessary		




	"""inserts a new node into the dictionary with corresponding key and value, starting at the max

	@type key: int
	@pre: key currently does not appear in the dictionary
	@param key: key of item that is to be inserted to self
	@type val: string
	@param val: the value of the item
	@rtype: (AVLNode,int,int)
	@returns: a 3-tuple (x,e,h) where x is the new node,
	e is the number of edges on the path between the starting node and new node before rebalancing,
	and h is the number of PROMOTE cases during the AVL rebalancing
	"""
	def finger_insert(self, key, val):
		self.size_count += 1
		# Empty tree case
		if self.root is None:
			self.root = AVLNode(key, val)
			self.root.left = AVLNode(None, None)
			self.root.right = AVLNode(None, None)
			self.root.height = 0
			self.max_node = self.root
			return self.root, 0, 0

		curr = self.max_node
		e = 1
		# Traverse up to find the correct ancestor
		while curr.parent is not None and curr.parent.key >= key:
			curr = curr.parent
			e += 1
		
		# now curr is the lowest ancestor of max_node with key less than or equal to key
		return self.insert_helper(curr, key, val, e)
		


	"""deletes node from the dictionary

	@type node: AVLNode
	@pre: node is a real pointer to a node in self
	"""
	def delete(self, node):
     
		self.size_count -= 1
  
		# update max_node if necessary
		if self.max_node == node:
			if node.left.is_real_node():
				self.max_node = node.left
				while self.max_node.right.is_real_node():
					self.max_node = self.max_node.right
			else:
				self.max_node = node.parent

		# 'y' will track where we start rebalancing from
		y = node.parent
  
		# Deletion logic to be implemented
		if not node.right.is_real_node() and not node.left.is_real_node(): #case 1: node is a leaf
			self.delete_case1(node, y)

		elif not node.right.is_real_node() or not node.left.is_real_node(): #case 2: node has one child
			self.delete_case2(node, y)
   
		elif node.right.is_real_node() and node.left.is_real_node(): #case 3: node has two children
			succ = self.successor(node)

			# If successor is the direct child of node, the parent becomes the node's position (succ)
        	# Otherwise, it's the successor's original parent.
			if succ.parent == node:
				y = succ
			else:
				y = succ.parent
    
			if not succ.right.is_real_node() and not succ.left.is_real_node(): #case 1: node is a leaf
				self.delete_case1(succ, succ.parent)
			else: #case 2: node has one child
				self.delete_case2(succ, succ.parent)
    
			#replace node with succ
			succ.parent = node.parent
			succ.left = node.left
			succ.right = node.right
			succ.height = node.height
			
			if succ.left.is_real_node():
				succ.left.parent = succ
			if succ.right.is_real_node():
				succ.right.parent = succ
			
			# update parents pointers
			if node.parent is None: # node is root
				self.root = succ
			else:
				if node.parent.left == node:
					node.parent.left = succ
				else:
					node.parent.right = succ

		# Rebalance the tree
		while y is not None:
			BF = y.left.height - y.right.height

			# Check if node is balanced
			if abs(BF) < 2:
				# if the height is unchanged, no further rebalancing is needed
				if y.height == 1 + max(y.left.height, y.right.height):
					return
				else:
					# Update height and move up the tree
					y.height = 1 + max(y.left.height, y.right.height)
					y = y.parent
			else:
				# Rebalance the tree
				self.rotation(y, BF)
				y = y.parent
			
		return	
	


	def successor(self, node):

		# if node is the max node, no successor
		if node == self.max_node:
			return None

		# if node has right child, his successor is the minimum in right subtree
		if node.right.is_real_node():
			curr = node.right
			while curr.left.is_real_node():
				curr = curr.left
			return curr
		
		# else, go up until we find a node which is left child of his parent
		y = node.parent
		while y is not None and node == y.right:
			node = y
			y = node.parent

		return y
	
	


	def delete_case1(self, node, y):
		if y is None: # node is root
			self.root = None
			self.max_node = None
			return

		dummy = AVLNode(None, None)
		dummy.parent = y
  
		if y.left == node:
			y.left = dummy
		else:
			y.right = dummy
		return

	def delete_case2(self, node, y):
     
		child = node.left if node.left.is_real_node() else node.right
  
		if y is None: # node is root
			self.root = child
			child.parent = None
			if self.max_node == node:
				self.max_node = child
			return

		if y.left == node:
			y.left = child
		else:
			y.right = child
		child.parent = y

	
	"""joins self with item and another AVLTree

	@type tree2: AVLTree 
	@param tree2: a dictionary to be joined with self
	@type key: int 
	@param key: the key separting self and tree2
	@type val: string
	@param val: the value corresponding to key
	@pre: all keys in self are smaller than key and all keys in tree2 are larger than key,
	or the opposite way
	"""
	def join(self, tree2, key, val):
		return


	"""splits the dictionary at a given node

	@type node: AVLNode
	@pre: node is in self
	@param node: the node in the dictionary to be used for the split
	@rtype: (AVLTree, AVLTree)
	@returns: a tuple (left, right), where left is an AVLTree representing the keys in the 
	dictionary smaller than node.key, and right is an AVLTree representing the keys in the 
	dictionary larger than node.key.
	"""
	def split(self, node):
		return None, None

	
	"""returns an array representing dictionary 

	@rtype: list
	@returns: a sorted list according to key of touples (key, value) representing the data structure
	"""
	def avl_to_array(self):
		return None


	"""returns the node with the maximal key in the dictionary

	@rtype: AVLNode
	@returns: the maximal node, None if the dictionary is empty
	"""
	def max_node(self):
		return self.max_node

	"""returns the number of items in dictionary 

	@rtype: int
	@returns: the number of items in dictionary 
	"""
	def size(self):
		return self.size_count	


	"""returns the root of the tree representing the dictionary

	@rtype: AVLNode
	@returns: the root, None if the dictionary is empty
	"""
	def get_root(self):
		return self.root
