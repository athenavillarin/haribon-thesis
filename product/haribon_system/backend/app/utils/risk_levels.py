"""
Risk level utility functions for consistent classification mapping.
Used for model training, validation, and comparing predictions with actual outcomes.
"""

# String to numeric mapping for risk levels
RISK_LEVEL_MAPPING = {
    "Low Risk": 1,
    "Moderate Risk": 2,
    "High Risk": 3
}

# Reverse mapping: numeric to string
RISK_LEVEL_REVERSE_MAPPING = {
    1: "Low Risk",
    2: "Moderate Risk",
    3: "High Risk"
}

# Valid risk level strings
VALID_RISK_LEVELS = list(RISK_LEVEL_MAPPING.keys())


def risk_level_to_numeric(risk_level: str) -> int:
    """
    Convert risk level string to numeric value.
    
    Args:
        risk_level: Risk level string ("Low Risk", "Moderate Risk", "High Risk")
        
    Returns:
        Numeric value (1, 2, or 3)
        
    Raises:
        ValueError: If risk_level is not a valid risk level
    """
    if risk_level not in RISK_LEVEL_MAPPING:
        raise ValueError(
            f"Invalid risk level: {risk_level}. Must be one of {VALID_RISK_LEVELS}"
        )
    return RISK_LEVEL_MAPPING[risk_level]


def numeric_to_risk_level(numeric_value: int) -> str:
    """
    Convert numeric value to risk level string.
    
    Args:
        numeric_value: Numeric risk value (1, 2, or 3)
        
    Returns:
        Risk level string
        
    Raises:
        ValueError: If numeric_value is not 1, 2, or 3
    """
    if numeric_value not in RISK_LEVEL_REVERSE_MAPPING:
        raise ValueError(
            f"Invalid numeric risk value: {numeric_value}. Must be 1, 2, or 3"
        )
    return RISK_LEVEL_REVERSE_MAPPING[numeric_value]


def is_valid_risk_level(risk_level: str) -> bool:
    """Check if a string is a valid risk level."""
    return risk_level in RISK_LEVEL_MAPPING


def normalize_risk_level(risk_level: str) -> str:
    """
    Normalize risk level string (ensures consistency).
    
    Args:
        risk_level: Input risk level (may have extra whitespace or casing variations)
        
    Returns:
        Normalized risk level string or original if invalid
    """
    normalized = risk_level.strip().title()
    # Handle common variations
    if normalized in RISK_LEVEL_MAPPING:
        return normalized
    return risk_level  # Return original if no match found


def compare_predictions(predicted_risk: str, actual_risk: str) -> dict:
    """
    Compare predicted risk level with actual outcome.
    
    Args:
        predicted_risk: Predicted risk level string
        actual_risk: Actual observed risk level string
        
    Returns:
        Dict with comparison results including:
        - correct: Boolean indicating if prediction matches actual
        - predicted_numeric: Numeric value of prediction
        - actual_numeric: Numeric value of actual
        - difference: Numeric difference (for retraining analysis)
    """
    try:
        pred_num = risk_level_to_numeric(predicted_risk)
        actual_num = risk_level_to_numeric(actual_risk)
        
        return {
            "correct": predicted_risk == actual_risk,
            "predicted": predicted_risk,
            "actual": actual_risk,
            "predicted_numeric": pred_num,
            "actual_numeric": actual_num,
            "difference": actual_num - pred_num,  # Positive = underpredicted, Negative = overpredicted
        }
    except ValueError as e:
        return {
            "error": str(e),
            "correct": False,
        }
