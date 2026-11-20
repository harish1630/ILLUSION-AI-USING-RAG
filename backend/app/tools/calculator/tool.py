"""Secure mathematical evaluation tool using Python AST. Never uses eval()."""

import ast
import operator
import math
from typing import Dict, Any, Union
from app.core.logging import logger
from app.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult


class SafeCalculator:
    """
    Evaluates basic math and common mathematical functions using AST parsing.
    Strictly forbids arbitrary code, variable assignment, attribute access, and imports.
    """

    # Supported binary operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }

    # Supported unary operators
    UNARY_OPERATORS = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    # Safe math functions
    FUNCTIONS = {
        "sqrt": math.sqrt,
        "pow": math.pow,
        "abs": abs,
        "round": round,
        "floor": math.floor,
        "ceil": math.ceil,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
    }

    # Safe constants
    CONSTANTS = {
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
    }

    @classmethod
    def evaluate(cls, expression: str) -> Union[int, float]:
        """Safely parses and evaluates an expression using an AST visitor."""
        clean_expr = expression.strip()
        if not clean_expr:
            raise ValueError("Empty mathematical expression.")

        if len(clean_expr) > 500:
            raise ValueError("Expression exceeds maximum allowed length (500 chars).")

        try:
            tree = ast.parse(clean_expr, mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Invalid mathematical syntax: {e}")

        return cls._eval_node(tree.body)

    @classmethod
    def _eval_node(cls, node: ast.AST) -> Union[int, float]:
        # Numbers (int / float)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")

        # Named constants like pi, e
        elif isinstance(node, ast.Name):
            name_lower = node.id.lower()
            if name_lower in cls.CONSTANTS:
                return cls.CONSTANTS[name_lower]
            raise ValueError(f"Disallowed variable or symbol: '{node.id}'")

        # Binary operations: a + b, a * b, etc.
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in cls.OPERATORS:
                raise ValueError(f"Unsupported binary operator: {op_type.__name__}")

            left = cls._eval_node(node.left)
            right = cls._eval_node(node.right)

            # Prevent denial of service via huge exponents (e.g., 99999 ** 99999)
            if op_type == ast.Pow:
                if isinstance(right, (int, float)) and right > 10000:
                    raise ValueError("Exponent too large (maximum allowed is 10,000).")
                if isinstance(left, (int, float)) and abs(left) > 1e10 and right > 100:
                    raise ValueError("Calculation would overflow numerical limits.")

            if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                raise ZeroDivisionError("Division by zero is undefined.")

            return cls.OPERATORS[op_type](left, right)

        # Unary operations: -x, +x
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in cls.UNARY_OPERATORS:
                raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
            operand = cls._eval_node(node.operand)
            return cls.UNARY_OPERATORS[op_type](operand)

        # Function calls: sqrt(16), abs(-5)
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only direct math function calls are permitted.")

            func_name = node.func.id.lower()
            if func_name not in cls.FUNCTIONS:
                raise ValueError(f"Unknown or disallowed function: '{func_name}()'")

            args = [cls._eval_node(arg) for arg in node.args]
            func = cls.FUNCTIONS[func_name]
            try:
                return func(*args)
            except Exception as e:
                raise ValueError(f"Error evaluating '{func_name}': {e}")

        else:
            raise ValueError(f"Security error: AST node '{type(node).__name__}' is strictly forbidden.")


class CalculatorTool(BaseTool):
    """Calculator tool providing secure evaluation of arithmetic and financial formulas."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="calculator",
            display_name="Calculator",
            description=(
                "Computes exact mathematical expressions, arithmetic, loans, percentage, subsidy calculations, "
                "budgets, and formulas without executing arbitrary Python or eval()."
            ),
            parameters=[
                ToolParameter(
                    name="expression",
                    type="string",
                    description="The mathematical expression to evaluate (e.g. '7500000 * 0.25', '1500000 / 12', 'sqrt(144)').",
                    required=True,
                )
            ],
            category="math",
            requires_auth=False,
            is_available=True,
        )

    async def execute(self, **kwargs) -> ToolResult:
        expression = kwargs.get("expression", "")
        if not expression:
            return ToolResult(
                tool_name="calculator",
                success=False,
                error="No expression provided for calculator.",
            )

        try:
            result = SafeCalculator.evaluate(str(expression))
            # Format nicely for integers vs floats
            formatted = f"{result:,}" if isinstance(result, int) else f"{result:,.4f}".rstrip("0").rstrip(".")
            return ToolResult(
                tool_name="calculator",
                success=True,
                data={
                    "expression": expression,
                    "result": result,
                    "formatted": formatted,
                },
                metadata={"raw_expression": expression},
            )
        except Exception as e:
            logger.warning(f"Calculator evaluation failed for '{expression}': {e}")
            return ToolResult(
                tool_name="calculator",
                success=False,
                error=str(e),
                metadata={"expression": expression},
            )
