from __future__ import annotations

import datetime
from typing import Union, List
from common import Type
from klass import KlassFile
from package import Package, PackageTemplateHelper
import javalang.tree as jtree
from common import Import
import os
import jinja2


class ImportHelper(object):
    """
    So far, only use this to resolve package name
    Still need to figure out how to get class names
    """
    def __init__(self, imp):
        self.imp = imp
        self.package_name = None
        self.class_name = None

        if isinstance(imp, str):
            parts = imp.split(".")
            if len(parts) == 1:
                self.class_name = None
                self.package_name = imp
            else:
                self.package_name = ".".join(imp.split(".")[:-1])
                self.class_name = imp.split(".")[-1]
        elif isinstance(imp, jtree.Import):
            # TODO - what about imp.static ?
            if imp.wildcard:
                self.package_name = ".".join(imp.path.split(".")[:-1])
            else:
                #self.class_name = imp.path.split(".")[-1]
                self.package_name = imp.path
        else:
            print(type(imp))
            raise Exception("imp is invalid type")

class TypeResolver(object):
    """
    Resolve a java type to a python annotated type

    Needs to be created in context of a class to determine its imports
    """
    def __init__(self, j2p: JavaToPython):
        self.j2p = j2p

    def convert_type(self, name):
        """
        Convert Java-type to Python-equivalent type

        Based on https://www.jython.org/jython-old-sites/archive/22/userguide.html
        :param name: type name (str)
        :return: python type represented as str
        """
        python_equivalents = {
            "java.lang.String": "str",
            "List[java.lang.Byte]": "bytearray",
            "java.lang.Int": "int",
            "java.lang.Double": "float",
            "java.lang.Short": "int",
            "java.lang.Float": "float",
            "java.lang.List": "list",
            "java.lang.Byte": "int",
            "java.lang.Char": "str",
            "java.lang.Boolean": "bool"  # This have to be ok...
        }

        if name in python_equivalents:
            return python_equivalents.get(name)
        else:
            return name

    def resolve_type(self, name, klassfile: Union[None, KlassFile] = None, imports: List[Union[str, jtree.Import]] = None):
        """
        Resolve full package name for class
        :param name: class
        :param imports: list of packages (str or Import instace) used to resolve classes
        :return: pkg.name.class
        """
        basic_types = {
            "int": "java.lang.Int",
            "byte": "java.lang.Byte",
            "boolean": "java.lang.Boolean",
            "char": "java.lang.Char",
            "double": "java.lang.Double",
            "float": "java.lang.Float",
            "long": "java.lang.Long",
            "short": "java.lang.Short"
        }

        if name in basic_types:
            return basic_types.get(name)

        if imports is None:
            imports = []

        if klassfile is not None:
            for imp in klassfile.imports:
                _imp = ImportHelper(imp.node.path)
                if j2p.has_package(_imp.package_name):
                    pkg = j2p.open_package(_imp.package_name)
                    if name in pkg.class_names:
                        return pkg.name + "." + name

        default_imports = ["java.lang.*"]
        imports.extend(default_imports)

        for imp in imports:
            package_name = ImportHelper(imp).package_name
            if j2p.has_package(package_name):
                pkg = j2p.open_package(package_name)
                if name in pkg.class_names:
                    return pkg.name + "." + name

        # Unable to find package for class
        return name

    def resolve_typehint(self, typeobj: Type, klassfile: KlassFile = None):
        if typeobj is None:
            return "None"
        if typeobj.has_children():
            if typeobj.is_reference() and typeobj.name == "List":
                return f"List[{self.resolve_typehint(typeobj.get_children())}]"
            else:
                return self.resolve_type(typeobj.name)
        else:
            if typeobj.is_basic():
                if typeobj.is_array():
                    return f"List[{self.resolve_type(typeobj.name, klassfile=klassfile)}]"
                else:
                    return self.resolve_type(typeobj.name)
            elif typeobj.is_reference():
                if typeobj.is_array():
                    return f"List[{self.resolve_type(typeobj.name, klassfile=klassfile)}]"
                else:
                    return self.resolve_type(typeobj.name, klassfile=klassfile)
            else:
                raise Exception("You have reached unreachable code!")

    def python_resolve(self, typeobj: Type, klassfile: KlassFile = None):
        """

        :param typeobj: Type object
        :param klassfile: Klass file
        :return: python equivalent type
        """

        if typeobj is None:
            return "None"
        if typeobj.has_children():
            if typeobj.is_reference() and typeobj.name == "List":
                return f"List[{self.python_resolve(typeobj.get_children())}]"
            else:
                return self.convert_type(self.resolve_type(typeobj.name, klassfile=klassfile))
        else:
            if typeobj.is_basic():
                if typeobj.is_array():
                    #return f"List[{self.convert_type(self.resolve_type(typeobj.name, klassfile=klassfile))}]"
                    converted_type = f"List[{self.resolve_type(typeobj.name, klassfile=klassfile)}]"
                    return self.convert_type(converted_type)
                    #return f"List[{self.convert_type(self.resolve_type(typeobj.name, klassfile=klassfile))}]"
                else:
                    return self.convert_type(self.resolve_type(typeobj.name))
            elif typeobj.is_reference():
                if typeobj.is_array():
                    return f"List[{self.convert_type(self.resolve_type(typeobj.name, klassfile=klassfile))}]"
                else:
                    return self.convert_type(self.resolve_type(typeobj.name, klassfile=klassfile))
            else:
                raise Exception("You have reached unreachable code!")


class PackageRenderer(object):
    def __init__(self, template_dir: str, type_resolver: TypeResolver, package: Package) -> PackageRenderer:
        self.package = package
        self.environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader(searchpath=template_dir)
        )
        self.type_resolver = type_resolver

        self.environment.filters["resolve_type"] = type_resolver.resolve_type
        self.environment.filters["resolve_typehint"] = type_resolver.resolve_typehint
        self.environment.filters["convert_type"] = type_resolver.convert_type
        self.environment.filters["python_resolve"] = type_resolver.python_resolve

    def render(self):
        template = self.environment.get_template("class.txt")

        return template.render(package=PackageTemplateHelper(self.package), now=datetime.datetime.utcnow)


class JavaToPython(object):
    def __init__(self, source_dir):
        if source_dir.endswith("/") or source_dir.endswith("\\"):
            source_dir = source_dir[:-1]
        self.source_dir = source_dir + os.sep
        if not os.path.isdir(self.source_dir):
            raise FileNotFoundError(f"Could not find source directory {self.source_dir}")

    def open_package(self, package_name):
        package_dir = self.source_dir + os.sep.join(package_name.split(".")) + os.sep
        if not os.path.isdir(package_dir):
            raise FileNotFoundError(f"Could not open package directory {package_dir}")

        pkg = Package(package_dir, package_name)
        return pkg

    def has_package(self, package_name):
        package_dir = self.source_dir + os.sep.join(package_name.split("."))
        if not os.path.isdir(package_dir):
            return False
        return True

    def get_type_resolver(self):
        return TypeResolver(self)

    def create_python_package(self, package_name):
        pkg = self.open_package(package_name)
        renderer = PackageRenderer(template_dir="templates/", type_resolver=self.get_type_resolver(), package=pkg)
        return renderer.render()



if __name__ == "__main__":
    import argparse
    import sys
    if sys.gettrace() is not None:
        print("Debugging...")
        j2p = JavaToPython("sources")
        pypackage = j2p.create_python_package("burp")
        print(pypackage)
        sys.exit()

    parser = argparse.ArgumentParser("Create Python Interface Class from Java Source Package")
    parser.add_argument("--sourcedir", type=str, help="directory where java packages are located", required=True)
    parser.add_argument("--package", type=str, help="Java Package to create python class from", required=True)
    parser.add_argument("--outfile", type=str, help="Filename to write python interface class to", required=False)

    args = parser.parse_args()
    #print(args)
    j2p = JavaToPython("sources")
    #resolver = j2p.get_type_resolver()
    #print(resolver.resolve_type("IScannerCheck", ["burp.*"]))
    pypackage = j2p.create_python_package(args.package)
    if args.outfile is None:
        print(pypackage)
    else:
        open(args.outfile,"w+", encoding="utf-8").write(pypackage)
