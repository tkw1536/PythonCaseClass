from CaseClass import AbstractCaseClass, CaseClass, InheritableCaseClass


class Tree(AbstractCaseClass):
    def __init__(self, value, *children):
        self.value = value
        self.children = children


class InternalNode(Tree):
    pass


class LeafNode(Tree):
    def __init__(self, value):
        super(LeafNode, self).__init__(value)


if __name__ == "__main__":
    tree = InternalNode(LeafNode[1], LeafNode[2], LeafNode[3])
    print(LeafNode(1) is LeafNode(1))