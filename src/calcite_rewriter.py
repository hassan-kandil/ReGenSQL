import os
import typing as t
import jpype as jp
import jpype.imports
from jpype.types import *

from dataclasses import dataclass
from src.utils.java_utils import to_python_list, to_java_string, to_java_bool, to_java_int, to_java_list


@dataclass
class CalciteRule:
    """Represents a Calcite optimization rule"""

    name: str
    type: str
    plan_before: str
    plan_after: str

    def __str__(self):
        return f"CalciteRule({self.name} - {self.type})"


@dataclass
class CalciteRewriteResult:
    """Represents the result of a rewrite operation"""

    query: str
    rules_applied: t.List[str]
    rewrite_time: float

    def __str__(self):
        return (
            f"RewriteResult(query={self.query}, rules_applied={self.rules_applied}, rewrite_time={self.rewrite_time})"
        )


class CalciteRewriter:
    """
    A class to handle SQL query rewriting using Java-based Calcite rewriting tool.
    Manages JVM initialization and provides methods for various rewriting operations.
    """

    def __init__(self, lib_dir: str = None, database: str = "PostgreSQL", schema: str = None):
        """
        Initialize the QueryRewriter with the specified library directory.

        Args:
            lib_dir: Path to the directory containing the Java libraries
        """
        if lib_dir is None:
            lib_dir = os.path.join(os.path.dirname(__file__), "../CalciteRewrite/out/artifacts/LearnedRewrite_jar")

        self.lib_dir = os.path.abspath(lib_dir)
        self._setup_java_environment()
        self._import_java_classes()
        self.database = database
        self.create_tables = [x for x in schema.split(";") if x.strip() != ""]

    def _setup_java_environment(self):
        """Configure JAVA environment for JPype"""
        classpath = []
        classpath.extend([os.path.join(self.lib_dir, jar) for jar in os.listdir(self.lib_dir)])

        if not jp.isJVMStarted():
            jp.startJVM(jp.getDefaultJVMPath(), classpath=classpath)

    def _import_java_classes(self):
        """Import required Java classes"""
        from rewriter import Rewriter, MyRules
        from learned import LearnedRewriter

        # Store references to Java classes
        self.Rewriter = Rewriter
        self.MyRules = MyRules
        self.LearnedRewriter = LearnedRewriter

    def _match_normal_rules(self, query: str, verbose: bool = True) -> t.List[t.Dict[str, str]]:
        """
        Match normal rewriting rules against the query.

        Args:
            query: SQL query string
            verbose: Enable verbose output (default: True)

        Returns:
            List of matched rules
        """
        return to_python_list(
            self.Rewriter.matchNormalRules(
                to_java_string(query),
                to_java_list(self.create_tables),
                to_java_string(self.database),
                to_java_bool(verbose),
            )
        )

    def _match_explore_rules(self, query: str, verbose: bool = True) -> t.List[t.Dict[str, str]]:
        """
        Match exploration rules against the query.

        Args:
            query: SQL query string
            verbose: Enable verbose output (default: True)

        Returns:
            List of matched rules
        """
        return to_python_list(
            self.Rewriter.matchExploreRules(
                to_java_string(query),
                to_java_list(self.create_tables),
                to_java_string(self.database),
                to_java_bool(verbose),
            )
        )

    def _match_all_rules(self, query: str, verbose: bool = True) -> t.List[t.Dict[str, str]]:
        """
        Match all available rules against the query.

        Args:
            query: SQL query string
            verbose: Enable verbose output

        Returns:
            List of all matched rules
        """
        return to_python_list(
            self.Rewriter.matchAllRules(
                to_java_string(query),
                to_java_list(self.create_tables),
                to_java_string(self.database),
                to_java_bool(verbose),
            )
        )

    def match_calcite_rules(self, query: str) -> t.List[CalciteRule]:
        rule_dicts = self._match_all_rules(query, self.create_tables)
        rules = [
            CalciteRule(
                name=str(r["name"]),
                type=str(r["type"]),
                plan_before=str(r["plan_before"]),
                plan_after=str(r["plan_after"]),
            )
            for r in rule_dicts
        ]
        return rules

    def rewrite(
        self,
        query: str,
        calcite_rules: t.List[CalciteRule],
        rounds: int = 1,
    ) -> CalciteRewriteResult:
        """
        Rewrite the query using specified rules.

        Args:
            query: SQL query string
            calcite_rules: List of CalciteRule objects to apply
            rounds: Number of rewriting rounds

        Returns:
            CalciteRewriteResult object containing the rewritten query and applied rules
        """
        rule_names = [r.name for r in calcite_rules]
        rewrite_result_obj = self.Rewriter.rewrite(
            to_java_string(query),
            to_java_list(self.create_tables),
            to_java_list(rule_names),
            to_java_int(rounds),
            to_java_string(self.database),
        )
        return CalciteRewriteResult(
            query=str(rewrite_result_obj.sql),
            rules_applied=[str(r) for r in rewrite_result_obj.rules],
            rewrite_time=float(rewrite_result_obj.time),
        )

    def get_normal_rules(self) -> t.List[str]:
        """
        Get a list of all available normal rules.

        Returns:
            Sorted list of normal rule names
        """
        normal_rules = sorted([str(r) for r in self.MyRules.NORMAL_RULES.keySet()])
        return normal_rules
