import os
import typing as t
import jpype as jp
import jpype.imports
from jpype.types import *

""" Configure JAVA environment for JPype """
classpath = []
lib_dir = os.path.join(os.path.dirname(__file__), "../../CalciteRewrite/out/artifacts/LearnedRewrite_jar")
abs_lib_dir = os.path.abspath(lib_dir)
classpath.extend([os.path.join(abs_lib_dir, jar) for jar in os.listdir(abs_lib_dir)])

if not jp.isJVMStarted():
    jp.startJVM(jp.getDefaultJVMPath(), classpath=classpath)

from java.util import ArrayList


def to_java_string(s: str) -> JString:
    return JString(s)


def to_java_bool(b: bool) -> JBoolean:
    return JBoolean(b)


def to_java_int(i: int) -> JInt:
    return JInt(i)


def to_java_list(lst: t.List) -> ArrayList:
    return ArrayList(lst)


def to_python_list(lst: ArrayList) -> t.List:
    return list(lst)
