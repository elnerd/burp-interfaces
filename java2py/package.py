import sys

from klass import KlassFile
from typing import List, Union
import os
import javalang



class Package(object):
    def __init__(self, pkg_dir, package_name):
        self.pkg_dir = pkg_dir
        self.package_name = package_name

    def list_class_names(self) -> List[str]:
        """
        Lists the classes that are found under a package (source directory)
        :return: List of classnames
        """
        filenames = list(filter(lambda filename: filename.endswith(".java"), os.listdir(self.pkg_dir)))
        return list(map(lambda filename: filename.removesuffix(".java"), filenames))

    def read_class_file(self, name: str) -> str:
        filename = self.pkg_dir + name + ".java"
        return open(filename, "r").read()

    def parse_class(self, name: str) -> Union[KlassFile,None]:
        try:
            jlang = javalang.parse.parse(self.read_class_file(name))
            return KlassFile(jlang, klass_name=name)
        except javalang.parser.JavaSyntaxError as exception:
            sys.stderr.write(f"could not parse class {name}\n")
            return None

    @property
    def class_names(self):
        return self.list_class_names()

    @property
    def name(self):
        return self.package_name


class PackageTemplateHelper(object):
    def __init__(self, package: Package):
        self.package = package

    @property
    def klass_names(self):
        return self.package.list_class_names()

    @property
    def klasses(self):
        klasses = []
        for class_name in self.klass_names:
            # HACK: need to put classes with inheritances last

            klassfile = self.package.parse_class(class_name)
            if klassfile is None:
                continue

            inheritance = klassfile.klass.inheritance
            if len(inheritance) == 1 and inheritance[0] == "object":
                klasses.insert(0, klassfile)
            else:
                klasses.append(klassfile)

        return klasses

    @property
    def imports(self):
        for klassfile in self.klasses:
            for imp in klassfile.imports:
                yield imp



if __name__ == "__main__":
    pkg = Package("sources/", "burp")
    #print(pkg.list_class_names())
    #print(pkg.read_class_file('IContextMenuFactory'))
    for _import in pkg.parse_class("IBurpExtender").imports:
        print(_import.python_module)
