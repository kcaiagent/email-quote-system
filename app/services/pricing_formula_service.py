"""
Pricing formula parsing and execution service
"""
import re
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class PricingFormulaService:
    """Service for parsing and executing pricing formulas"""
    
    @staticmethod
    def execute_formula(
        formula: str,
        area: float,
        base_price: float = 0,
        rate: float = 0.05,
        **kwargs
    ) -> float:
        """
        Execute a pricing formula
        
        Args:
            formula: Formula string (e.g., "base_price + (area * rate)")
            area: Area in square inches
            base_price: Base price (if not in formula context)
            rate: Rate per square inch (if not in formula context)
            **kwargs: Additional variables for formula
        
        Returns:
            Calculated price
        """
        if not formula:
            # Default formula
            return area * rate
        
        try:
            # Replace variables with values
            formula_context = {
                "area": area,
                "base_price": base_price,
                "rate": rate,
                **kwargs
            }
            
            # Safe evaluation of formula
            result = PricingFormulaService._safe_eval(formula, formula_context)
            
            return float(result) if result is not None else 0.0
            
        except Exception as e:
            logger.error(f"Error executing formula '{formula}': {e}")
            # Fallback to simple calculation
            return area * rate
    
    @staticmethod
    def validate_formula(formula: str) -> tuple[bool, Optional[str]]:
        """
        Validate a pricing formula
        
        Returns:
            (is_valid, error_message)
        """
        if not formula or not formula.strip():
            return False, "Formula is empty"
        
        try:
            # Try to parse the formula with dummy values
            PricingFormulaService._safe_eval(
                formula,
                {"area": 100, "base_price": 0, "rate": 0.05}
            )
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def _safe_eval(expression: str, context: Dict[str, Any]) -> Any:
        """
        Safely evaluate a Python expression with allowed operations only
        
        Only allows:
        - Basic math operations (+, -, *, /, **, %)
        - Comparison operations (<, >, <=, >=, ==, !=)
        - Logical operations (and, or, not)
        - Conditional expressions (if/else)
        - Numbers and variables from context
        """
        # Remove whitespace
        expression = expression.strip()
        
        # Replace variable names with their values
        # Sort by length (longest first) to avoid partial replacements
        sorted_vars = sorted(context.keys(), key=len, reverse=True)
        
        # Create a safe context with only allowed operations
        safe_context = {
            "__builtins__": {},
            "abs": abs,
            "min": min,
            "max": max,
            "round": round,
            "pow": pow,
        }
        
        # Replace variables in expression with their string representations
        # This is safer than direct substitution
        for var_name in sorted_vars:
            var_value = context[var_name]
            # Use regex to replace variable names (whole words only)
            pattern = r'\b' + re.escape(var_name) + r'\b'
            expression = re.sub(pattern, str(var_value), expression)
        
        # Validate expression doesn't contain dangerous operations
        dangerous_patterns = [
            r'import\s+',
            r'__\w+__',
            r'exec\s*\(',
            r'eval\s*\(',
            r'open\s*\(',
            r'file\s*\(',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                raise ValueError(f"Dangerous operation detected in formula: {pattern}")
        
        # Evaluate the expression
        try:
            result = eval(expression, safe_context, {})
            return result
        except Exception as e:
            # Try to handle conditional expressions manually
            if "if" in expression.lower():
                return PricingFormulaService._eval_conditional(expression, context)
            raise
    
    @staticmethod
    def _eval_conditional(expression: str, context: Dict[str, Any]) -> Any:
        """
        Evaluate conditional expressions like "if condition then value1 else value2"
        """
        # Normalize expression
        expression = expression.strip()
        
        # Handle Python ternary: value1 if condition else value2
        if " if " in expression and " else " in expression:
            parts = expression.split(" if ", 1)
            if len(parts) == 2:
                true_value = parts[0].strip()
                condition_and_false = parts[1]
                
                if " else " in condition_and_false:
                    condition, false_value = condition_and_false.split(" else ", 1)
                    condition = condition.strip()
                    false_value = false_value.strip()
                    
                    # Evaluate condition
                    cond_result = PricingFormulaService._safe_eval(condition, context)
                    
                    if cond_result:
                        return PricingFormulaService._safe_eval(true_value, context)
                    else:
                        return PricingFormulaService._safe_eval(false_value, context)
        
        # Handle if-then-else format
        if "then" in expression.lower() and "else" in expression.lower():
            # Simple if-then-else pattern
            match = re.match(r'if\s+(.+?)\s+then\s+(.+?)\s+else\s+(.+)', expression, re.IGNORECASE)
            if match:
                condition, true_value, false_value = match.groups()
                cond_result = PricingFormulaService._safe_eval(condition.strip(), context)
                
                if cond_result:
                    return PricingFormulaService._safe_eval(true_value.strip(), context)
                else:
                    return PricingFormulaService._safe_eval(false_value.strip(), context)
        
        raise ValueError(f"Could not parse conditional expression: {expression}")
    
    @staticmethod
    def parse_formula_variables(formula: str) -> list[str]:
        """
        Extract variable names from a formula
        
        Returns:
            List of variable names used in the formula
        """
        if not formula:
            return []
        
        # Common variables
        common_vars = ["area", "base_price", "rate", "length", "width"]
        
        found_vars = []
        for var in common_vars:
            if re.search(r'\b' + re.escape(var) + r'\b', formula):
                found_vars.append(var)
        
        return found_vars
    
    @staticmethod
    def normalize_formula(formula: str) -> str:
        """
        Normalize formula format (handle common variations)
        """
        if not formula:
            return ""
        
        formula = formula.strip()
        
        # Replace common variations
        formula = re.sub(r'\s+', ' ', formula)  # Normalize whitespace
        
        return formula


# Singleton instance
pricing_formula_service = PricingFormulaService()








