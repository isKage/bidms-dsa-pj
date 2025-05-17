class BTreeNode:

    def __init__(self, t, leaf):
        # Constructor for BTreeNode
        self.t = t  # Minimum degree (defines the range for the number of keys)
        self.leaf = leaf  # Is true when the node is leaf, otherwise false
        self.keys = [0] * (2 * t - 1)  # An array of keys
        self.C = [None] * (2 * t)  # An array of child pointers
        self.n = 0  # Current number of keys

    def find_key(self, k):
        # A utility function to find the index of the first key greater than or equal to k
        idx = 0
        while idx < self.n and self.keys[idx] < k:
            idx += 1
        return idx

    def remove(self, k):
        # A function to remove key k from the sub-tree rooted with this node
        idx = self.find_key(k)

        if idx < self.n and self.keys[idx] == k:
            if self.leaf:
                self.remove_from_leaf(idx)
            else:
                self.remove_from_non_leaf(idx)
        else:
            if self.leaf:
                print(f"The key {k} does not exist in the tree")
                return

            flag = idx == self.n
            if self.C[idx].n < self.t:
                self.fill(idx)

            if flag and idx > self.n:
                self.C[idx - 1].remove(k)
            else:
                self.C[idx].remove(k)

    def remove_from_leaf(self, idx):
        # A function to remove the idx-th key from this node, which is a leaf node
        for i in range(idx + 1, self.n):
            self.keys[i - 1] = self.keys[i]
        self.n -= 1

    def remove_from_non_leaf(self, idx):
        # A function to remove the idx-th key from this node, which is a non-leaf node
        k = self.keys[idx]

        if self.C[idx].n >= self.t:
            pred = self.get_pred(idx)
            self.keys[idx] = pred
            self.C[idx].remove(pred)
        elif self.C[idx + 1].n >= self.t:
            succ = self.get_succ(idx)
            self.keys[idx] = succ
            self.C[idx + 1].remove(succ)
        else:
            self.merge(idx)
            self.C[idx].remove(k)

    def get_pred(self, idx):
        # A function to get the predecessor of the key at the idx-th position in the node
        cur = self.C[idx]
        while not cur.leaf:
            cur = cur.C[cur.n]

        return cur.keys[cur.n - 1]

    def get_succ(self, idx):
        # A function to get the successor of the key at the idx-th position in the node
        cur = self.C[idx + 1]
        while not cur.leaf:
            cur = cur.C[0]

        return cur.keys[0]

    def fill(self, idx):
        # A function to fill child C[idx] which has fewer than t-1 keys
        if idx != 0 and self.C[idx - 1].n >= self.t:
            self.borrow_from_prev(idx)
        elif idx != self.n and self.C[idx + 1].n >= self.t:
            self.borrow_from_next(idx)
        else:
            if idx != self.n:
                self.merge(idx)
            else:
                self.merge(idx - 1)

    def borrow_from_prev(self, idx):
        # A function to borrow a key from C[idx-1] and insert it into C[idx]
        child, sibling = self.C[idx], self.C[idx - 1]

        for i in range(child.n - 1, -1, -1):
            child.keys[i + 1] = child.keys[i]

        if not child.leaf:
            for i in range(child.n, -1, -1):
                child.C[i + 1] = child.C[i]

        child.keys[0] = self.keys[idx - 1]

        if not child.leaf:
            child.C[0] = sibling.C[sibling.n]

        self.keys[idx - 1] = sibling.keys[sibling.n - 1]

        child.n += 1
        sibling.n -= 1

    def borrow_from_next(self, idx):
        # A function to borrow a key from C[idx+1] and place it in C[idx]
        child, sibling = self.C[idx], self.C[idx + 1]

        child.keys[child.n] = self.keys[idx]

        if not child.leaf:
            child.C[child.n + 1] = sibling.C[0]

        self.keys[idx] = sibling.keys[0]

        for i in range(1, sibling.n):
            sibling.keys[i - 1] = sibling.keys[i]

        if not sibling.leaf:
            for i in range(1, sibling.n + 1):
                sibling.C[i - 1] = sibling.C[i]

        child.n += 1
        sibling.n -= 1

    def merge(self, idx):
        # A function to merge C[idx] with C[idx+1]
        child, sibling = self.C[idx], self.C[idx + 1]

        child.keys[self.t - 1] = self.keys[idx]

        for i in range(sibling.n):
            child.keys[i + self.t] = sibling.keys[i]

        if not child.leaf:
            for i in range(sibling.n + 1):
                child.C[i + self.t] = sibling.C[i]

        for i in range(idx + 1, self.n):
            self.keys[i - 1] = self.keys[i]

        for i in range(idx + 2, self.n + 1):
            self.C[i - 1] = self.C[i]

        child.n += sibling.n + 1
        self.n -= 1

    def insert_non_full(self, k):
        # A utility function to insert a new key in this node
        # The assumption is that the node must be non-full when this function is called
        i = self.n - 1

        if self.leaf:
            while i >= 0 and self.keys[i] > k:
                self.keys[i + 1] = self.keys[i]
                i -= 1

            self.keys[i + 1] = k
            self.n += 1
        else:
            while i >= 0 and self.keys[i] > k:
                i -= 1

            i += 1
            if self.C[i].n == (2 * self.t - 1):
                self.split_child(i, self.C[i])

                if self.keys[i] < k:
                    i += 1

            self.C[i].insert_non_full(k)

    def split_child(self, i, y):
        # A utility function to split the child y of this node
        # i is the index of y in the child array C[]
        z = BTreeNode(y.t, y.leaf)
        z.n = self.t - 1

        for j in range(self.t - 1):
            z.keys[j] = y.keys[j + self.t]

        if not y.leaf:
            for j in range(self.t):
                z.C[j] = y.C[j + self.t]

        y.n = self.t - 1

        for j in range(self.n, i, -1):
            self.C[j + 1] = self.C[j]

        self.C[i + 1] = z

        for j in range(self.n - 1, i - 1, -1):
            self.keys[j + 1] = self.keys[j]

        self.keys[i] = y.keys[self.t - 1]
        self.n += 1

    def traverse(self):
        # A function to traverse all nodes in a subtree rooted with this node
        i = 0
        while i < self.n:
            if not self.leaf:
                self.C[i].traverse()
            print(self.keys[i], end=" ")
            i += 1

        if not self.leaf:
            self.C[i].traverse()


class BTree:
    def __init__(self, t):
        # Constructor for BTree
        self.root = None  # Pointer to the root node
        self.t = t  # Minimum degree

    def traverse(self):
        # A function to traverse the B-tree
        if self.root:
            self.root.traverse()
            print()

    def search(self, k):
        # A function to search for a key in the B-tree
        return None if not self.root else self.root.search(k)

    def insert(self, k):
        # The main function that inserts a new key in the B-tree
        if not self.root:
            self.root = BTreeNode(self.t, True)
            self.root.keys[0] = k
            self.root.n = 1
        else:
            if self.root.n == (2 * self.t - 1):
                s = BTreeNode(self.t, False)
                s.C[0] = self.root
                s.split_child(0, self.root)

                i = 0
                if s.keys[0] < k:
                    i += 1

                s.C[i].insert_non_full(k)
                self.root = s
            else:
                self.root.insert_non_full(k)

    def remove(self, k):
        # The main function that removes a key from the B-tree
        if not self.root:
            print("The tree is empty")
            return

        self.root.remove(k)

        if self.root.n == 0:
            tmp = self.root
            if self.root.leaf:
                self.root = None
            else:
                self.root = self.root.C[0]

            del tmp


# Driver program to test above functions
if __name__ == "__main__":
    b_tree = BTree(3)

    keys_to_insert = [2, 3, 4, 5, 6, 12, 1, 7, 8, 9, 10, 11]

    for key in keys_to_insert:
        b_tree.insert(key)

    print("Before Deletion:", end=" ")
    b_tree.traverse()

    b_tree.remove(5)

    print("After Deletion:", end=" ")
    b_tree.traverse()
