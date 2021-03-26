import re
from typing import Optional, List

import bs4
import html

pattern_block_comment = r"^\/\*+(?P<body>.*?)\*\/$"

re_block = re.compile(pattern_block_comment, re.S)
re_stars = re.compile(r"^\s*\*[\t ]*", re.M)

class ChainDecoder(object):
    def __init__(self):
        self.comment = ""
        self.chain = []

    def decode(self, comment):
        for decoder in self.chain:
            comment = decoder(comment)
        return comment

    def add_decoder(self, decoder):
        self.chain.append(decoder)


class JavaDocumentation(ChainDecoder):
    re_double_newlines = re.compile(r"((\r\n)|(\n)){3,}",re.DOTALL|re.S)

    def __init__(self, docstr):
        super().__init__()
        self.original_docstr = docstr
        self.new_docstr = None  # type: Optional[str,None]

        self.add_decoder(self.cleanup)
        self.add_decoder(self.untag)
        self.add_decoder(self.unquote)

    def parse(self):
        if self.new_docstr is not None:
            return
        self.new_docstr = self.decode(self.original_docstr)


    def remove_double_newlines(self, comment: str):
        """
        remove double newlines - used by absorbing classes
        """
        old = comment
        while (new := self.re_double_newlines.sub("",comment)) != old:
            old = new
        return new

    def cleanup(self, comment: str):
        """
        /**
         * removes the dash-star patterns from comments
        */
        :return: comment without comment tags
        """
        s = comment.strip()
        if s.startswith("/*"):
            match = re_block.match(s)
            if match is None:
                raise ValueError("Expected c-style block comment, but re_block expression did not find comment body")
            body = match.groupdict()["body"]
            return re_stars.sub("", body)
        elif s.startswith("//"):
            return s.replace("//", "", 1)
        else:
            return s
            #raise ValueError("Unable to clean up comment!")


    def untag(self, comment):
        """
        Strip tags away but keep tag <b>content</b>
        :return:
        """
        return comment
        soup = bs4.BeautifulSoup(comment, features="html.parser")
        for tag in soup.findAll(True):
            s = ""
            for c in tag.contents:
                if not isinstance(c, bs4.NavigableString):
                    c = self.untag(str(c))
                s += c
            tag.replaceWith(s)
        return str(soup)


    def unquote(self, comment):
        """
        decode html quotes such as &amp;
        Repeats decoding until no more quotes
        :return: html-unquoted comment
        """
        old = comment
        while (unquoted := html.unescape(old)) != old:
            old = unquoted
        return unquoted

class KeyValue(object):
    def __init__(self, key=None, value=None):
        self._key = key
        self._value = value

    @property
    def name(self):
        return self.key

    @name.setter
    def name(self, name):
        self.key = name

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

class ParamHint(KeyValue):
    pass

class ReturnHint(KeyValue):
    pass

class ExceptionHint(KeyValue):
    pass


class MethodDocumentation(JavaDocumentation):
    re_params = re.compile(
        r"@param\s+(?P<parameter_name>[a-zA-Z0-9_]+)\s+(?P<parameter_comment>.*?)(?:(?=\n@)|$)",
        re.S|re.DOTALL)
    re_return = re.compile(r"@return\s+(?P<return_comment>.*?)(?:(?=\n@)|$)",re.S|re.DOTALL)
    re_exception = re.compile(r"@exception\s+(?P<exception>[a-zA-Z0-9]+)\s+(?P<exception_comment>.*?)(?:(?=\n@)|$)",
                              re.S|re.DOTALL)

    def __init__(self, docstr):
        super().__init__(docstr)
        self.add_decoder(self.absorb_params)
        self.add_decoder(self.absorb_return_type)
        self.add_decoder(self.absorb_exceptions)
        self.add_decoder(self.remove_double_newlines)

        self.parameters = []  # type: List[ParamHint]
        self.return_type = None  # type: Optional[ReturnHint,None]
        self.exceptions = []  # type: List[ExceptionHint]

    def absorb_return_type(self, comment):
        s = comment
        # Only expect one match
        #match = self.re_return.match(comment)
        match = self.re_return.search(comment)
        if match is not None:
            return_comment = match.groupdict()["return_comment"]
            self.return_type = ReturnHint(None, return_comment)
            s = s[0:match.start()] + s[match.end():]
        return s

    def absorb_params(self, comment):
        s = comment
        while (match := self.re_params.search(s)) != None:
            param_name = match.groupdict()["parameter_name"]
            param_comment = match.groupdict()["parameter_comment"]
            self.parameters.append(ParamHint(param_name, param_comment))
            s = s[0:match.start()] + s[match.end():]
        return s

    def absorb_exceptions(self, comment):
        s = comment
        while (match := self.re_exception.search(s)) != None:
            exception = match.groupdict()["exception"]
            comment = match.groupdict()["exception_comment"]
            self.exceptions.append(ExceptionHint(exception, comment))
            s = s[0:match.start()] + s[match.end():]
        return s

class DocumentationTemplateFacade(object):
    javadoc_instance = None  # type: JavaDocumentation
    javadoc_class = JavaDocumentation

    def __init__(self, docstr):
        self.javadoc_instance = self.javadoc_class(docstr)
        self.javadoc_instance.parse()

    def __str__(self):
        return self.javadoc_instance.new_docstr

    def to_string(self):
        return str(self)

class MethodDocumentationTemplateFacade(DocumentationTemplateFacade):
    javadoc_class = MethodDocumentation
    javadoc_instance = None  # type: MethodDocumentation

    @property
    def parameters(self):
        return self.javadoc_instance.parameters

    @property
    def return_type(self):
        return self.javadoc_instance.return_type

    @property
    def exceptions(self):
        return self.javadoc_instance.exceptions





class ClassDocumentation(JavaDocumentation):
    def __init__(self, docstr):
        super().__init__(docstr)

class ClassDocumentationTemplateFacade(DocumentationTemplateFacade):
    javadoc_class = JavaDocumentation
    javadoc_instance = None  # type: JavaDocumentation


class ConstantDocumentation(JavaDocumentation):
    javadoc_class = JavaDocumentation
    javadoc_instance = None  # type: JavaDocumentation

