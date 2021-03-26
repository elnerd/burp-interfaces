from __future__ import annotations

from typing import Union, List
import javalang.tree as jtree


class Import(object):
    node: jtree.Import

    def __init__(self, node):
        self.node = node

    @property
    def package_name(self):
        if self.node.wildcard:
            return self.node.path.rstrip(".*")
        else:
            """
            TODO
            This an be a burp.IScannerInsertionPoint.INS_BODY !!!
            Need to talk to package manager to see if there really is a package with this name
            """
            return self.node.path

    @property
    def python_module(self):
        if self.node.wildcard:
            import_name = self.node.path.rstrip(".*")
            return f"{import_name}"
        else:
            return f"{self.node.path}"


class Type(object):
    node: Union[jtree.ReferenceType, jtree.BasicType]

    def __init__(self, node):
        assert isinstance(node, jtree.ReferenceType) or isinstance(node, jtree.BasicType)
        self.node = node

    @property
    def name(self):
        return self.node.name

    def is_basic(self):
        """
        Is type a basic type (int, float, long, ...)
        :return: bool
        """
        return isinstance(self.node, jtree.BasicType)

    def is_reference(self):
        """
        Is type a reference to another java class?
        :return: bool
        """
        return isinstance(self.node, jtree.ReferenceType)

    def is_array(self):
        """
        Is the type an type[] array?
        :return: bool
        """
        return self.node is not None and len(self.node.dimensions) == 1 and self.node.dimensions[0] is None

    def has_children(self):
        return hasattr(self.node, "arguments") and self.node.arguments is not None

    def get_children(self) -> Type:
        if self.has_children():
            return Type(self.node.arguments[0].children[0])
        else:
            raise Exception("Ooops, you forgot to check if this type actually have any children (it dont)")
