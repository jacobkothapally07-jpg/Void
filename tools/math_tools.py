import ast
import math
import operator
from typing import Any

# Allowed binary operators
_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# Allowed unary operators
_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# Allowed math functions & constants
_MATH_FUNCS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "log": math.log,
    "ln": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
    "ceil": math.ceil,
    "floor": math.floor,
}

def _eval_node(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value!r}")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BINOPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if op_type == ast.Pow and (abs(right) > 1000 or abs(left) > 10000):
            raise ValueError("Exponent or base too large")
        return _BINOPS[op_type](left, right)

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARYOPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        return _UNARYOPS[op_type](_eval_node(node.operand))

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Function call must be a simple name")
        func_name = node.func.id
        if func_name not in _MATH_FUNCS or not callable(_MATH_FUNCS[func_name]):
            raise ValueError(f"Unknown or non-callable function: {func_name}")
        args = [_eval_node(arg) for arg in node.args]
        return _MATH_FUNCS[func_name](*args)

    if isinstance(node, ast.Name):
        if node.id in _MATH_FUNCS and not callable(_MATH_FUNCS[node.id]):
            return _MATH_FUNCS[node.id]
        raise ValueError(f"Unknown variable: {node.id}")

    raise ValueError(f"Unsupported expression node: {type(node).__name__}")

def calculate_expression(expression: str) -> dict:
    """
    Safely evaluates complex mathematical expressions using AST.
    Handles arithmetic, trigonometry, square roots, logs, powers, and constants.
    """
    clean_expr = expression.strip()
    try:
        tree = ast.parse(clean_expr, mode="eval")
        result = _eval_node(tree.body)
        return {
            "status": "success",
            "expression": clean_expr,
            "result": result,
            "detail": f"Calculation complete, Sir: {clean_expr} = {result}"
        }
    except Exception as e:
        return {"status": "error", "message": f"Calculation failed: {str(e)}"}
