"""Unit tests for the calculator tool.

Tests arithmetic accuracy, error handling, and code injection prevention.
"""

import pytest
from app.agents.tools.calculator import calculator, get_calculator_tool


class TestCalculator:
    """Test calculator tool arithmetic accuracy."""

    def test_basic_addition(self):
        """Test simple addition."""
        result = calculator.invoke({"expression": "2 + 2"})
        assert result == "4"

    def test_basic_subtraction(self):
        """Test simple subtraction."""
        result = calculator.invoke({"expression": "10 - 3"})
        assert result == "7"

    def test_basic_multiplication(self):
        """Test simple multiplication."""
        result = calculator.invoke({"expression": "6 * 7"})
        assert result == "42"

    def test_basic_division(self):
        """Test simple division."""
        result = calculator.invoke({"expression": "20 / 4"})
        assert result == "5.0"

    def test_scope_addition(self):
        """Test typical scope emissions addition (the main use case)."""
        result = calculator.invoke({"expression": "2300000 + 1100000 + 8500000"})
        assert result == "11900000"

    def test_scope_addition_with_decimals(self):
        """Test scope emissions with decimal values."""
        result = calculator.invoke({"expression": "2.3e6 + 1.1e6 + 8.5e6"})
        assert float(result) == pytest.approx(11900000, rel=0.001)

    def test_percentage_change(self):
        """Test YoY percentage calculation."""
        result = calculator.invoke({"expression": "((2450000 - 2300000) / 2450000) * 100"})
        assert float(result) == pytest.approx(6.122, rel=0.01)

    def test_percentage_decrease(self):
        """Test percentage decrease calculation."""
        result = calculator.invoke({"expression": "((2300000 - 2450000) / 2450000) * 100"})
        assert float(result) == pytest.approx(-6.122, rel=0.01)

    def test_discrepancy_percent(self):
        """Test discrepancy percentage calculation."""
        result = calculator.invoke({"expression": "abs(11900000 - 12000000) / 12000000 * 100"})
        assert float(result) == pytest.approx(0.833, rel=0.01)

    def test_compound_reduction(self):
        """Test annual reduction rate calculation (compound)."""
        # 42% reduction over 11 years: (1-0.42)^(1/11)
        result = calculator.invoke({"expression": "(1 - 0.42) ** (1/11)"})
        assert float(result) == pytest.approx(0.953, rel=0.01)

    def test_annual_reduction_rate(self):
        """Test annual reduction rate expressed as percentage."""
        # Required annual rate = 1 - (1-0.42)^(1/11)
        result = calculator.invoke({"expression": "(1 - (1 - 0.42) ** (1/11)) * 100"})
        assert float(result) == pytest.approx(4.68, rel=0.05)

    def test_target_value_calculation(self):
        """Test target value calculation."""
        # 42% reduction from 2.5M = 2.5M * (1 - 0.42) = 1.45M
        result = calculator.invoke({"expression": "2500000 * (1 - 0.42)"})
        assert float(result) == pytest.approx(1450000, rel=0.001)

    def test_parentheses_order(self):
        """Test order of operations with parentheses."""
        result = calculator.invoke({"expression": "(2 + 3) * 4"})
        assert result == "20"

    def test_exponentiation(self):
        """Test power operator."""
        result = calculator.invoke({"expression": "2 ** 10"})
        assert result == "1024"

    def test_nested_parentheses(self):
        """Test nested parentheses."""
        result = calculator.invoke({"expression": "((10 + 5) * 2) / 3"})
        assert result == "10.0"

    def test_division_by_zero(self):
        """Test division by zero returns error message."""
        result = calculator.invoke({"expression": "1 / 0"})
        assert "Division by zero" in result

    def test_invalid_expression_syntax(self):
        """Test invalid syntax returns error."""
        result = calculator.invoke({"expression": "2 + * 3"})
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_invalid_expression_import(self):
        """Test import statements are blocked."""
        result = calculator.invoke({"expression": "import os"})
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_code_injection_blocked_import(self):
        """Verify SimpleEval blocks __import__ code injection."""
        result = calculator.invoke({"expression": "__import__('os').system('ls')"})
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_code_injection_blocked_eval(self):
        """Verify eval calls are blocked."""
        result = calculator.invoke({"expression": "eval('1+1')"})
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_code_injection_blocked_exec(self):
        """Verify exec calls are blocked."""
        result = calculator.invoke({"expression": "exec('print(1)')"})
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_code_injection_blocked_open(self):
        """Verify file access is blocked."""
        result = calculator.invoke({"expression": "open('/etc/passwd').read()"})
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_abs_function(self):
        """Test abs() function is available."""
        result = calculator.invoke({"expression": "abs(-5)"})
        assert result == "5"

    def test_abs_with_expression(self):
        """Test abs() with complex expression."""
        result = calculator.invoke({"expression": "abs(-100 + 50)"})
        assert result == "50"

    def test_round_function(self):
        """Test round() function is available."""
        result = calculator.invoke({"expression": "round(3.14159, 2)"})
        assert result == "3.14"

    def test_round_to_integer(self):
        """Test round() to integer."""
        result = calculator.invoke({"expression": "round(3.7)"})
        assert result == "4"

    def test_min_function(self):
        """Test min() function."""
        result = calculator.invoke({"expression": "min(1, 2, 3)"})
        assert result == "1"

    def test_max_function(self):
        """Test max() function."""
        result = calculator.invoke({"expression": "max(1, 2, 3)"})
        assert result == "3"

    def test_min_max_negative(self):
        """Test min/max with negative numbers."""
        assert calculator.invoke({"expression": "min(-5, -10, 0)"}) == "-10"
        assert calculator.invoke({"expression": "max(-5, -10, 0)"}) == "0"

    def test_float_precision(self):
        """Test float precision is reasonable (10 decimal places)."""
        result = calculator.invoke({"expression": "1 / 3"})
        assert float(result) == pytest.approx(0.3333333333, rel=1e-9)

    def test_scientific_notation(self):
        """Test scientific notation is handled."""
        result = calculator.invoke({"expression": "1e6 + 2e6"})
        assert float(result) == 3000000

    def test_large_numbers(self):
        """Test large number handling."""
        result = calculator.invoke({"expression": "1000000000 * 1000"})
        assert result == "1000000000000"

    def test_small_decimals(self):
        """Test small decimal handling."""
        result = calculator.invoke({"expression": "0.00001 * 0.00001"})
        assert float(result) == pytest.approx(1e-10, rel=1e-5)


class TestGetCalculatorTool:
    """Test tool factory function."""

    def test_returns_callable_tool(self):
        """Test that factory returns a tool with invoke method."""
        tool = get_calculator_tool()
        assert callable(tool.invoke)

    def test_tool_has_description(self):
        """Test that tool has a description for LLM."""
        tool = get_calculator_tool()
        assert "mathematical" in tool.description.lower()

    def test_tool_has_name(self):
        """Test that tool has the correct name."""
        tool = get_calculator_tool()
        assert tool.name == "calculator"

    def test_tool_is_same_instance(self):
        """Test that factory returns the same tool instance."""
        tool1 = get_calculator_tool()
        tool2 = get_calculator_tool()
        assert tool1 is tool2

    def test_tool_description_includes_examples(self):
        """Test that tool description includes usage examples."""
        tool = get_calculator_tool()
        assert "expression" in tool.description.lower()

    def test_tool_invocation_via_factory(self):
        """Test tool can be invoked via factory."""
        tool = get_calculator_tool()
        result = tool.invoke({"expression": "5 + 5"})
        assert result == "10"


class TestCalculatorEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_expression(self):
        """Test empty expression handling."""
        result = calculator.invoke({"expression": ""})
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_whitespace_only(self):
        """Test whitespace-only expression."""
        result = calculator.invoke({"expression": "   "})
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_leading_zeros(self):
        """Test numbers with leading zeros are not allowed in Python."""
        # Python doesn't allow leading zeros (octal syntax conflict)
        result = calculator.invoke({"expression": "007 + 003"})
        # Should return an error since Python doesn't allow leading zeros
        assert "error" in result.lower() or "10" == result

    def test_negative_numbers(self):
        """Test negative number handling."""
        result = calculator.invoke({"expression": "-5 + -3"})
        assert result == "-8"

    def test_double_negative(self):
        """Test double negative."""
        result = calculator.invoke({"expression": "--5"})
        assert result == "5"

    def test_very_long_expression(self):
        """Test handling of long expressions."""
        # Sum of 1 to 10
        result = calculator.invoke({"expression": "1+2+3+4+5+6+7+8+9+10"})
        assert result == "55"

    def test_mixed_operators(self):
        """Test expression with mixed operators."""
        result = calculator.invoke({"expression": "10 + 5 * 2 - 3 / 1"})
        assert result == "17.0"

    def test_integer_division(self):
        """Test integer division result type."""
        result = calculator.invoke({"expression": "10 / 5"})
        assert result == "2.0"  # Division always returns float

    def test_floor_division_not_supported(self):
        """Test floor division operator handling."""
        # SimpleEval may or may not support //
        result = calculator.invoke({"expression": "10 // 3"})
        # Should either work or give an error, not crash
        assert result == "3" or "error" in result.lower() or result == "3.0"

    def test_modulo_not_supported(self):
        """Test modulo operator handling."""
        result = calculator.invoke({"expression": "10 % 3"})
        # Should either work or give an error
        assert result == "1" or "error" in result.lower()
