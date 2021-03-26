import sys

import javalang.tree as jtree
from method import Method
from typing import List, Union
from common import Import
from common import Type
from doc import ClassDocumentation, ClassDocumentationTemplateFacade, JavaDocumentation


class Constant(object):
    def __init__(self, node):
        assert isinstance(node, jtree.ConstantDeclaration)
        self.node = node

    @property
    def name(self):
        return self.node.declarators[0].name

    @property
    def value(self):
        if isinstance(self.node.declarators[0].initializer, jtree.MemberReference):
            return self.node.declarators[0].initializer.member
        elif isinstance(self.node.declarators[0].initializer, jtree.Literal):
            return self.node.declarators[0].initializer.value
        else:
            return "None"

    @property
    def type(self):
        return Type(self.node.type)

    @property
    def documentation(self):
        if not hasattr(self.node, "documentation"):
            return None
        if self.node.documentation == None:
            return None
        else:
            return JavaDocumentation(self.node.documentation)


class KlassFile(object):
    java: jtree.CompilationUnit

    def __init__(self, tree, klass_name):
        assert isinstance(tree, jtree.CompilationUnit)
        self.tree = tree
        self.klass_name = klass_name

    @property
    def imports(self) -> List[Import]:
        if not hasattr(self.tree, "imports"):
            return []
        return list(map(Import, self.tree.imports))

    @property
    def klass(self):
        """
        We only want to grab one public class

        If we have multiple class definitions in the same file, retrieve by priority
        1. class name with same name as filename
        2. class name with public modifier set
        :return: Klass
        """
        _klasses = list(
                filter(
                    lambda _type: isinstance(
                        _type, (jtree.InterfaceDeclaration, jtree.ClassDeclaration, jtree.AnnotationDeclaration)
                    ), self.tree.types)
        )
        if len(_klasses) == 0:
            sys.stderr.write(f"No class found in KlassFile \"{self.klass_name}\"\n")
            return None
            #raise Exception(f"No class found in KlassFile {self.klass_name}")
        elif len(_klasses) > 1:
            klass = list(filter(lambda _klass: _klass.name == self.klass_name, _klasses))
            if len(klass) == 1:
                return Klass(klass[0])
            else:
                sys.stderr.write(f"Too many classes found in KlassFile \"{self.klass_name}\"")
        else:
            return Klass(_klasses[0])

    @property
    def documentation(self):
        # Seems like javalang have a bug and do not return documentation for the class file
        # TODO investigate and report issue
        if not hasattr(self.tree.package, "documentation"):
            return None
        if self.tree.package.documentation is None:
            return None
        else:
            return JavaDocumentation(self.tree.package.documentation)


class Klass(object):
    java: jtree.InterfaceDeclaration

    def __init__(self, node):
        assert isinstance(node, (jtree.InterfaceDeclaration,jtree.ClassDeclaration, jtree.AnnotationDeclaration))
        self.node = node


    @property
    def name(self):
        return self.node.name

    @property
    def methods(self) -> List[Method]:
        if not hasattr(self.node, "methods"):
            return []

        return list(map(Method, self.node.methods))

    @property
    def constants(self) -> List[Constant]:
        if not hasattr(self.node, "fields"):
            return []
        return list(map(Constant, filter(lambda field: isinstance(field, jtree.ConstantDeclaration), self.node.fields)))

    @property
    def documentation(self) -> Union[ClassDocumentationTemplateFacade, None]:
        if not hasattr(self.node, "documentation"):
            return ClassDocumentationTemplateFacade("")
        if self.node.documentation is None:
            return ClassDocumentationTemplateFacade("")
        else:
            return ClassDocumentationTemplateFacade(self.node.documentation)

    @property
    def inheritance(self) -> List[str]:
        extensions = []
        if hasattr(self.node, "extends") and self.node.extends is not None:
            for extension in self.node.extends:
                extensions.append(extension.name)
        else:
            extensions.append("object")
        return extensions
