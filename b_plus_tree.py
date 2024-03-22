import typing as t


log_info = print


class Node:
    def __init__(self):
        self.tree: t.Optional['Tree'] = None
        self.leaf: bool = False
        # keys 就是存的索引，用来查找节点的
        self.keys: list[int] = []
        # children 就是存的子节点的引用，用来查找子节点的
        self.children: list['Node'] = []
        # 叶子节点的 rows 是真正的数据
        self.rows: list[int] = []
        # prev 和 next 是为了叶子节点的双向链表
        self.prev: t.Optional['Node'] = None
        self.next: t.Optional['Node'] = None

    @classmethod
    def new(cls, tree: 'Tree', leaf: bool):

        r = cls()
        r.tree = tree
        r.leaf = leaf

        return r

    def full(self):
        return len(self.keys) == 2 * self.tree.degree - 1

    def enough(self):
        tree = self.tree
        degree = tree.degree

        return len(self.keys) >= degree - 1

    def can_borrow(self):
        tree = self.tree
        degree = tree.degree

        return len(self.keys) >= degree

    # 分裂内部节点
    def split_child(self, child_index: int):
        tree = self.tree
        degree = tree.degree

        # 加载被拆分节点，node_old
        node_old = self.children[child_index]
        # 创建新节点，node_new，装载被拆分数据
        node_new = Node.new(tree, node_old.leaf)
        # 为新节点，node_new，装载 keys
        node_new.keys = node_old.keys[degree:]
        # 如果被拆分节点为叶子节点
        if node_new.leaf:
            # 父节点插入新节点的最小 key
            self.keys.insert(child_index, node_new.keys[0])
            # 被拆分节点装载 keys
            node_old.keys = node_old.keys[:degree]
            # 新节点装载 prev_page_index
            node_new.prev = node_old
            # 如果被拆分节点的右侧节点不为空
            if node_old.next is not None:
                # 加载被拆分节点右侧节点
                node_old_next_node = node_old.next
                # 新节点装载 next_page_index
                node_new.next = node_old_next_node
                # 被拆分节点的右侧节点装载 prev_page_index
                node_old_next_node.prev = node_new
            # 被拆分节点装载 next_leaf
            node_old.next = node_new
            # 新节点装载 rows
            node_new.rows = node_old.rows[degree:]
            # 被拆分节点装载 rows
            node_old.rows = node_old.rows[:degree]
        # 如果被拆分节点为节点内部节点
        else:
            # 父节点插入被拆分节点的中间 key，为了保证增序
            self.keys.insert(child_index, node_old.keys[degree - 1])
            # 被拆分节点装载 keys
            node_old.keys = node_old.keys[:degree - 1]
            # 新节点装载 page_indices
            node_new.children = node_old.children[degree:]
            # 被拆分节点装载 page_indices
            node_old.children = node_old.children[:degree]
        # 父节点 page_indices 插入新节点
        self.children.insert(child_index + 1, node_new)

    def insert(self, key: t.Union[int, str, float], row: int):
        tree = self.tree

        i = len(self.keys) - 1
        if self.leaf:

            # 这里是从后往前找到第一个比 key 小的 key 的位置
            while i >= 0 and key < self.keys[i]:
                i = i - 1
            i = i + 1

            self.keys.insert(i, key)
            self.rows.insert(i, row)
        else:

            while i >= 0 and key < self.keys[i]:
                i = i - 1
            i = i + 1

            child = self.children[i]
            if child.full():
                self.split_child(i)
                # 如果 key 大于分裂后的 key，就往右边走
                if key > self.keys[i]:
                    i = i + 1
            child = self.children[i]
            child.insert(key, row)

    def delete(self, key: t.Union[int, str, float]):
        tree = self.tree

        removed_key = None
        replace_key = None

        try:
            i = self.keys.index(key)

            if self.leaf:

                removed_key = self.keys.pop(i)

                if i < len(self.keys):
                    # i < len(self.keys) 说明 key 不是最后一个
                    replace_key = self.keys[i]
                elif self.next is not None:
                    # 如果 key 是最后一个，就找下一个节点的第一个 key
                    next_node = self.next
                    replace_key = next_node.keys[0]
                else:
                    # 如果 key 是最后一个，而且没有下一个节点，就是空了
                    replace_key = None

                self.rows.pop(i)

            else:
                # 这里是 key 同时在当前节点和子节点的情况
                child = self.children[i + 1]

                # 递归删除
                removed_key, replace_key = child.delete(key)
                self.repair_child(i + 1, removed_key, replace_key)
        except ValueError:
            # 如果 key 不在当前节点，就去子节点找
            if self.leaf:
                log_info(f'Node.delete, key <{key}> not found')
            else:
                i = 0
                n = len(self.keys)
                while i < n and key >= self.keys[i]:
                    i = i + 1

                child = self.children[i]

                removed_key, replace_key = child.delete(key)
                self.repair_child(i, removed_key, replace_key)

        return removed_key, replace_key

    # 重平衡子节点（子节点经过删除后，可能会不符合要求）
    def repair_child(self, child_index, removed_key, replace_key):
        tree = self.tree

        child = self.children[child_index]

        # remove_key 是子节点删除的 key
        # 如果 remove_key 在当前节点，就用 replace_key 替换
        # 这里替换父节点的key是为了保证增序
        if removed_key in self.keys and replace_key is not None:
            i = self.keys.index(removed_key)
            self.keys[i] = replace_key

        if child.enough():
            return

        # child 经过删除操作后，如果不符合要求，就需要调整 rebalance
        left_child = self.children[child_index - 1] if child_index > 0 else None
        right_child = self.children[child_index + 1] if child_index < len(self.children) - 1 else None

        # 如果左侧节点可以借
        if child_index > 0 and left_child is not None and left_child.can_borrow():
            self.borrow_from_left(child_index)
        elif child_index < len(self.children) - 1 and right_child is not None and right_child.can_borrow():
            # 如果右侧节点可以借
            self.borrow_from_right(child_index)
        else:
            # 合并子节点
            if child_index < len(self.children) - 1:
                # 如果右侧节点不为空，就合并右侧节点
                self.merge_right_child(child_index)
            else:
                # 否则就合并左侧节点
                self.merge_right_child(child_index - 1)

    # 跟左节点借数据
    def borrow_from_left(self, child_index):
        tree = self.tree

        child = self.children[child_index]
        # 左侧节点
        child_left = self.children[child_index - 1]

        if child.leaf:
            # 直接把左侧节点的最后一个 key 和 row 插入到 child 的第一个位置
            # 因为叶子节点 key 可以重复，所以可以直接插入，后面直接替换父节点的 key 就好了。
            child.keys.insert(0, child_left.keys.pop(-1))
            child.rows.insert(0, child_left.rows.pop(-1))
            # 父节点的 key 替换，保证增序
            self.keys[child_index - 1] = child.keys[0]
        else:
            # 这里就是把父节点的 key 插入到 child 的第一个位置，为了保证增序
            # 而没有直接把左侧节点的最后一个 key 插入到 child 的第一个位置
            # 因为内部节点的 key 是不能重复的，所以需要先把父节点的 key 插入到 child 的第一个位置
            child.keys.insert(0, self.keys[child_index - 1])
            # 把左侧节点的最后一个 节点插入到 child 的第一个位置
            child.children.insert(0, child_left.children.pop(-1))
            # 父节点的 key 替换成左侧节点的最后一个key，保证增序
            self.keys[child_index - 1] = child_left.keys.pop(-1)

    def borrow_from_right(self, child_index):
        tree = self.tree

        child = self.children[child_index]
        # 右侧节点
        child_right = self.children[child_index + 1]

        if child.leaf:
            # 把右侧节点的第一个 key 和 row 插入到 child 的最后一个位置
            child.keys.append(child_right.keys.pop(0))
            child.rows.append(child_right.rows.pop(0))
            # 父节点的 key 替换，保证增序
            self.keys[child_index] = child_right.keys[0]
        else:
            # 把父节点的 key 插入到 child 的最后一个位置，为了保证增序
            child.keys.append(self.keys[child_index])
            child.children.append(child_right.children.pop(0))
            # 父节点的 key 替换成右侧节点的第一个key，保证增序
            self.keys[child_index] = child_right.keys.pop(0)

    # 合并右侧节点
    def merge_right_child(self, child_index):
        tree = self.tree

        child = self.children[child_index]
        # 右侧节点
        child_right = self.children[child_index + 1]
        # 删掉右侧节点的引用
        self.children.pop(child_index + 1)

        if child.leaf:
            # 因为要合并右侧节点，keys[child_index] 是比右侧节点的 key 要小的，
            # 所以要删掉 keys[child_index]
            self.keys.pop(child_index)
            child.next = child_right.next
            if child.next is not None:
                child_next_node = child.next
                child_next_node.prev = child
        else:
            # 不是叶子节点，就把父节点的 key 插入到 child 的最后一个位置
            child.keys.append(self.keys.pop(child_index))

        # 把右侧节点的 keys 和 rows 合并到 child
        child.keys.extend(child_right.keys)
        if child.leaf:
            child.rows.extend(child_right.rows)
        else:
            child.children.extend(child_right.children)


class Tree:
    def __init__(self, degree: int = 2):
        self.degree: int = degree
        self.root: t.Optional[Node] = None

    def init_root(self):
        self.root = Node.new(self, True)

    def split_root(self):
        # 做一个没有 key 只有一个 children 的节点来做新 root
        # root split 了之后，b plus tree 的高度才会增长
        # 新增一个内部节点，然后把原来的 root 作为它的子节点
        node_new = Node.new(self, False)
        node_new.children = [self.root]
        self.root = node_new
        self.root.split_child(0)

    def insert(self, key: t.Union[int, str, float], row: int):
        # 如果 root 满了就 split
        if self.root.full():
            self.split_root()
        self.root.insert(key, row)

    def delete(self, key: t.Union[int, str, float]):

        self.root.delete(key)
        # 根节点为空，重新选择根节点
        if len(self.root.keys) == 0 and (not self.root.leaf):
            self.root = self.root.children[0]


def __main():
    tree = Tree()
    tree.init_root()
    for i in range(1, 10):
        tree.insert(i, i)


if __name__ == '__main__':
    __main()