from __future__ import annotations
from typing import Union, List

import javalang.tree as jtree
from common import Type


class Parameter(object):
    node: jtree.FormalParameter

    def __init__(self, node):
        assert isinstance(node, jtree.FormalParameter)
        self.node = node

    @property
    def type(self):
        return Type(self.node.type)

    @property
    def name(self):
        return self.node.name


class Method(object):
    node: jtree.MethodDeclaration

    def __init__(self, node):
        assert isinstance(node, jtree.MethodDeclaration)
        self.node = node

    @property
    def name(self):
        reserved_method_names = ["yield", "def", "return"]
        name = self.node.name
        if self.node.name in reserved_method_names:
            name += "_"
        return name

    @property
    def return_type(self):
        if self.node.return_type is None:
            return None
        return Type(self.node.return_type)

    @property
    def parameters(self):
        for parameter in self.node.parameters:
            yield Parameter(parameter)

    @property
    def parameter_names(self) -> List[str]:
        """
        return list of parameter names for this method
        """
        out = ["self"]
        # TODO get a full list of keywords that cannot be used as parameter names
        reserved_keywords = ["from", "import", "in", "def"]
        for parameter in self.parameters:
            name = parameter.name
            if parameter.name in reserved_keywords:
                name += "_"
            out.append(name)
        #out.extend([parameter.name for parameter in self.parameters])

        #out.replaceall("from", "_from")
        return out

    @property
    def documentation(self):
        from doc import MethodDocumentation, MethodDocumentationTemplateFacade
        if not hasattr(self.node, "documentation"):
            return None
        if self.node.documentation is None:
            return None
        else:
            return MethodDocumentationTemplateFacade(
                self.node.documentation
            )

