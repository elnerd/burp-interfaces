===============
burp-interfaces
===============

Installation
============

::

    pip2 install burp

Usage
=====

Now you should be able to import burp and receive typing hints!

::

    # Burp need to load each class explicitly
    from burp import IBurpExtender, IScannerCheck

    # This allow us to get typing hints for all burp classes in our IDE
    from burp import *

    class BurpExtender(IBurpExtender, IScannerCheck):
        def registerExtenderCallbacks(self, callbacks):  # type: (IBurpExtenderCallbacks) -> ()
            print "Loading plugin"
            callbacks.registerScannerCheck(self)

        def doPassiveScan(self, baseRequestResponse):  # type: (IHttpRequestResponse) -> List[IScanIssue]
            return []

        def doActiveScan(self, baseRequestResponse, insertionPoint):  # type: (IHttpRequestResponse, IScannerInsertionPoint) -> List[IScanIssue]
            return []



Documentation
=============

This is a python implementation of https://portswigger.net/burp/extender/api/

The purpose of this module is to provide typing hints (annotations) to your IDE.

NB. Do not include this module with your burp plugin

Known Issues
============

* Multiple signatures not supported in Python

python do not support multiple signatures. In many cases typing hints support multiple signatures.
When this is not the case, the methods will have an extra optional parameter called hey_check_docs to remind you that
there are multiple signatures for the given method.


