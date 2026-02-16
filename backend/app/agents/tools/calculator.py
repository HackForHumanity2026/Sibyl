"""Calculator tool for safe mathematical expression evaluation.

Uses SimpleEval for sandboxed arithmetic without code injection risks.
Exposed as a LangChain tool for LLM invocation during quantitative validation.
"""

from simpleeval import simple_eval, InvalidExpression
from langchain_core.tools import tool


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression safely.

    Use this tool for ALL arithmetic calculations - never calculate mentally.
    Supports: +, -, *, /, **, (), and decimal numbers.

    Examples:
        calculator("2300000 + 1100000 + 8500000")  -> "11900000"
        calculator("((2450000 - 2300000) / 2450000) * 100")  -> "6.12..."
        calculator("abs(11900000 - 12000000) / 12000000 * 100")  -> "0.83..."
        calculator("(1 - 0.42) ** 11")  -> "0.00111..."

    Args:
        expression: A mathematical expression string

    Returns:
        The numerical result as a string, or an error message
    """
    try:
        # SimpleEval provides safe evaluation without code injection
        result = simple_eval(
            expression,
            functions={"abs": abs, "round": round, "min": min, "max": max},
        )
        # Round to 10 decimal places for cleaner output
        if isinstance(result, float):
            return str(round(result, 10))
        return str(result)
    except InvalidExpression as e:
        return f"Invalid expression: {str(e)}"
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Calculation error: {str(e)}"


def get_calculator_tool():
    """Return the calculator tool for binding to an LLM."""
    return calculator
