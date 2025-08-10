import os
import typing as t

import jpype as jp
from jpype.types import *
import jpype.imports

# zip -d LearnedRewrite.jar META-INF/DUMMY.SF
# zip -d LearnedRewrite.jar META-INF/DUMMY.DSA
""" Configure JAVA environment for JPype """
classpath = []
lib_dir = os.path.join(os.path.dirname(__file__), "../../CalciteRewrite/out/artifacts/LearnedRewrite_jar")
abs_lib_dir = os.path.abspath(lib_dir)
classpath.extend([os.path.join(abs_lib_dir, jar) for jar in os.listdir(abs_lib_dir)])

if not jp.isJVMStarted():
    jp.startJVM(jp.getDefaultJVMPath(), classpath=classpath)

from rewriter import MyRules, Rewriter, RewriteResult
from src.utils.java_utils import to_java_bool, to_java_int, to_java_list, to_java_string, to_python_list


def match_normal_rules(
    query: str, create_tables: t.List[str], database: str = "PostgreSQL", verbose: bool = True
) -> t.List[t.Dict[str, str]]:
    return to_python_list(
        Rewriter.matchNormalRules(
            to_java_string(query), to_java_list(create_tables), to_java_string(database), to_java_bool(verbose)
        )
    )


def match_explore_rules(
    query: str, create_tables: t.List[str], database: str = "PostgreSQL", verbose: bool = True
) -> t.List[t.Dict[str, str]]:
    return to_python_list(
        Rewriter.matchExploreRules(
            to_java_string(query), to_java_list(create_tables), to_java_string(database), to_java_bool(verbose)
        )
    )


def match_all_rules(
    query: str, create_tables: t.List[str], database: str = "PostgreSQL", verbose: bool = True
) -> t.List[t.Dict[str, str]]:
    return to_python_list(
        Rewriter.matchAllRules(
            to_java_string(query), to_java_list(create_tables), to_java_string(database), to_java_bool(verbose)
        )
    )


def rewrite(
    query: str, create_tables: t.List[str], rule_names: t.List[str], rounds: int, database: str = "PostgreSQL"
) -> RewriteResult:
    return Rewriter.rewrite(
        to_java_string(query),
        to_java_list(create_tables),
        to_java_list(rule_names),
        to_java_int(rounds),
        to_java_string(database),
    )



def get_normal_rules() -> t.List[str]:
    normal_rules = sorted([str(r) for r in MyRules.NORMAL_RULES.keySet()])
    return normal_rules
