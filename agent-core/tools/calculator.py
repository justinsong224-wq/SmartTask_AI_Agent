"""
计算器工具
职责：安全执行数学表达式，返回计算结果
使用方式：result = await calculator("123 * 456 + 100")
"""

import ast
import math
import operator


# ── 白名单：只允许这些操作符，防止代码注入 ──────────────
ALLOWED_OPERATORS = {
    ast.Add:      operator.add,
    ast.Sub:      operator.sub,
    ast.Mult:     operator.mul,
    ast.Div:      operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod:      operator.mod,
    ast.Pow:      operator.pow,
    ast.USub:     operator.neg,   # 负号
    ast.UAdd:     operator.pos,
}

# ── 白名单：允许调用的数学函数 ──────────────────────────
ALLOWED_FUNCTIONS = {
    "abs": abs, "round": round,
    "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "pi": math.pi, "e": math.e,
    "ceil": math.ceil, "floor": math.floor,
    "pow": math.pow, "factorial": math.factorial,
}


def _safe_eval(node):
    """
    递归安全求值 AST 节点
    只允许白名单内的操作，拒绝任何系统调用
    """
    if isinstance(node, ast.Constant):          # 数字/字符串常量
        return node.value
    elif isinstance(node, ast.BinOp):           # 二元运算：a + b
        op = ALLOWED_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"不支持的运算符: {type(node.op).__name__}")
        return op(_safe_eval(node.left), _safe_eval(node.right))
    elif isinstance(node, ast.UnaryOp):         # 一元运算：-a
        op = ALLOWED_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"不支持的一元运算符: {type(node.op).__name__}")
        return op(_safe_eval(node.operand))
    elif isinstance(node, ast.Call):            # 函数调用：sqrt(2)
        func_name = node.func.id if isinstance(node.func, ast.Name) else None
        if func_name not in ALLOWED_FUNCTIONS:
            raise ValueError(f"不允许调用函数: {func_name}")
        args = [_safe_eval(a) for a in node.args]
        return ALLOWED_FUNCTIONS[func_name](*args)
    elif isinstance(node, ast.Name):            # 常量名：pi, e
        if node.id in ALLOWED_FUNCTIONS:
            return ALLOWED_FUNCTIONS[node.id]
        raise ValueError(f"不允许的变量: {node.id}")
    else:
        raise ValueError(f"不支持的表达式类型: {type(node).__name__}")


async def calculator(expression: str) -> str:
    """
    安全计算数学表达式
    :param expression: 数学表达式字符串，如 "123 * 456" 或 "sqrt(2) + pi"
    :return: 计算结果字符串
    """
    # 清理输入：去除多余空格，替换中文符号
    expression = expression.strip()
    expression = expression.replace("×", "*").replace("÷", "/").replace("，", ",")

    try:
        # 解析为 AST（不执行，只解析语法树）
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)

        # 格式化输出：整数去掉小数点，浮点保留合理精度
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        elif isinstance(result, float):
            result = round(result, 10)

        return f"计算结果：{expression} = {result}"

    except ZeroDivisionError:
        return "计算错误：除数不能为零"
    except ValueError as e:
        return f"表达式错误：{str(e)}"
    except Exception as e:
        return f"计算失败：{str(e)}"