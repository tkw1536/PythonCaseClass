from CaseClass import AbstractCaseClass

class Tree(AbstractCaseClass):
    def __init__(self, value, *children):
        self.value = value
        self.childs = children


class InternalNode(Tree):
    pass


class LeafNode(Tree):
    def __init__(self, value):
        super(LeafNode, self).__init__(value)


if __name__ == '__main__':
    t = InternalNode(10, LeafNode(1), LeafNode(1))
    print(t)
    print(t.case_params.children)