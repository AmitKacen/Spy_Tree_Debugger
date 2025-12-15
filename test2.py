from test_avl import AVLTree
if __name__ == "__main__":
    tree = AVLTree()
    values = [6, 7, 8, 5, 10]
    for value in values:
        tree.insert(value, "a")
    tree.delete(7)
    print("fdfdfdf")