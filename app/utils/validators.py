"""
Input validation utilities for the Personal Finance ML Backend.

This module provides comprehensive validation for API inputs,
handling edge cases and providing user-friendly error messages.
"""
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, model_validator


class DateRangeValidator(BaseModel):
    """Validator for date ranges."""
    
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    @model_validator(mode='after')
    def validate_date_range(self):
        """Validate date range logic."""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date must be before or equal to end_date")
            
            # Check if date range is too large
            if (self.end_date - self.start_date).days > 730:  # 2 years
                raise ValueError("Date range cannot exceed 2 years")
        
        # Check if dates are in the future
        today = date.today()
        if self.start_date and self.start_date > today:
            raise ValueError("start_date cannot be in the future")
        if self.end_date and self.end_date > today:
            raise ValueError("end_date cannot be in the future")
        
        return self


def validate_user_id(user_id: int) -> int:
    """
    Validate user ID.
    
    Args:
        user_id: User ID to validate
        
    Returns:
        Validated user ID
        
    Raises:
        ValueError: If user_id is invalid
    """
    if user_id <= 0:
        raise ValueError("user_id must be a positive integer")
    if user_id > 2147483647:  # Max INT in PostgreSQL
        raise ValueError("user_id is too large")
    return user_id


def validate_months_ahead(months_ahead: int, max_months: int = 24) -> int:
    """
    Validate months ahead parameter.
    
    Args:
        months_ahead: Number of months to predict
        max_months: Maximum allowed months
        
    Returns:
        Validated months_ahead
        
    Raises:
        ValueError: If months_ahead is invalid
    """
    if months_ahead <= 0:
        raise ValueError("months_ahead must be a positive integer")
    if months_ahead > max_months:
        raise ValueError(f"months_ahead cannot exceed {max_months}")
    return months_ahead


def validate_amount(amount: float, allow_negative: bool = False) -> float:
    """
    Validate monetary amount.
    
    Args:
        amount: Amount to validate
        allow_negative: Whether to allow negative amounts
        
    Returns:
        Validated amount
        
    Raises:
        ValueError: If amount is invalid
    """
    if not allow_negative and amount < 0:
        raise ValueError("amount must be non-negative")
    if abs(amount) > 1e15:  # Reasonable upper limit
        raise ValueError("amount is too large")
    if amount is None or amount != amount:  # Check for NaN
        raise ValueError("amount must be a valid number")
    return round(amount, 2)


def validate_percentage(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    Validate percentage value.
    
    Args:
        value: Percentage to validate (0.0 to 1.0)
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Validated percentage
        
    Raises:
        ValueError: If percentage is invalid
    """
    if value < min_val or value > max_val:
        raise ValueError(f"percentage must be between {min_val} and {max_val}")
    return value


def validate_category(category: str, allowed_categories: Optional[List[str]] = None) -> str:
    """
    Validate category name.
    
    Args:
        category: Category to validate
        allowed_categories: List of allowed categories (optional)
        
    Returns:
        Validated category
        
    Raises:
        ValueError: If category is invalid
    """
    if not category or not category.strip():
        raise ValueError("category cannot be empty")
    
    category = category.strip()
    
    if len(category) > 100:
        raise ValueError("category name is too long (max 100 characters)")
    
    if allowed_categories and category not in allowed_categories:
        raise ValueError(f"category must be one of: {', '.join(allowed_categories)}")
    
    return category


def validate_confidence_level(confidence_level: float) -> float:
    """
    Validate confidence level.
    
    Args:
        confidence_level: Confidence level (0.0 to 1.0)
        
    Returns:
        Validated confidence level
        
    Raises:
        ValueError: If confidence_level is invalid
    """
    if confidence_level <= 0 or confidence_level >= 1:
        raise ValueError("confidence_level must be between 0 and 1 (exclusive)")
    
    # Common confidence levels
    common_levels = [0.90, 0.95, 0.99]
    if confidence_level not in common_levels:
        # Round to 2 decimal places
        confidence_level = round(confidence_level, 2)
    
    return confidence_level


def validate_goal_data(
    target_amount: float,
    current_savings: float,
    goal_date: Optional[date] = None,
    monthly_savings: Optional[float] = None
) -> Dict[str, Any]:
    """
    Validate goal planning data.
    
    Args:
        target_amount: Goal target amount
        current_savings: Current savings amount
        goal_date: Target date for goal (optional)
        monthly_savings: Monthly savings amount (optional)
        
    Returns:
        Dictionary with validated data
        
    Raises:
        ValueError: If data is invalid
    """
    # Validate amounts
    target_amount = validate_amount(target_amount)
    current_savings = validate_amount(current_savings)
    
    if target_amount <= current_savings:
        raise ValueError("target_amount must be greater than current_savings")
    
    # Validate goal date
    if goal_date:
        today = date.today()
        if goal_date <= today:
            raise ValueError("goal_date must be in the future")
        
        # Check if goal date is too far in the future (e.g., 30 years)
        max_date = today + timedelta(days=365 * 30)
        if goal_date > max_date:
            raise ValueError("goal_date is too far in the future (max 30 years)")
    
    # Validate monthly savings
    if monthly_savings is not None:
        monthly_savings = validate_amount(monthly_savings)
        if monthly_savings <= 0:
            raise ValueError("monthly_savings must be positive")
    
    return {
        "target_amount": target_amount,
        "current_savings": current_savings,
        "goal_date": goal_date,
        "monthly_savings": monthly_savings
    }


def validate_budget_data(
    total_budget: float,
    categories: Dict[str, float]
) -> Dict[str, Any]:
    """
    Validate budget data.
    
    Args:
        total_budget: Total budget amount
        categories: Dictionary of category budgets
        
    Returns:
        Dictionary with validated data
        
    Raises:
        ValueError: If data is invalid
    """
    # Validate total budget
    total_budget = validate_amount(total_budget)
    if total_budget <= 0:
        raise ValueError("total_budget must be positive")
    
    # Validate categories
    if not categories:
        raise ValueError("categories cannot be empty")
    
    validated_categories = {}
    category_sum = 0.0
    
    for category, amount in categories.items():
        category = validate_category(category)
        amount = validate_amount(amount)
        
        if amount < 0:
            raise ValueError(f"budget for category '{category}' cannot be negative")
        
        validated_categories[category] = amount
        category_sum += amount
    
    # Check if category budgets exceed total budget
    if category_sum > total_budget * 1.1:  # Allow 10% tolerance
        raise ValueError("sum of category budgets exceeds total budget")
    
    return {
        "total_budget": total_budget,
        "categories": validated_categories
    }


def validate_historical_data_requirement(data_points: int, min_required: int = 3) -> None:
    """
    Validate that sufficient historical data is available.
    
    Args:
        data_points: Number of data points available
        min_required: Minimum required data points
        
    Raises:
        ValueError: If insufficient data
    """
    if data_points < min_required:
        raise ValueError(
            f"Insufficient historical data: found {data_points} months, "
            f"need at least {min_required} months for analysis"
        )


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input to prevent injection attacks.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
        
    Raises:
        ValueError: If string is too long
    """
    if not value:
        return ""
    
    # Strip whitespace
    value = value.strip()
    
    # Check length
    if len(value) > max_length:
        raise ValueError(f"string too long (max {max_length} characters)")
    
    # Remove potentially dangerous characters
    # (For now, we just validate - proper escaping is handled by SQLAlchemy)
    dangerous_patterns = ["--", ";", "/*", "*/", "xp_", "sp_"]
    for pattern in dangerous_patterns:
        if pattern in value.lower():
            raise ValueError(f"string contains potentially dangerous pattern: {pattern}")
    
    return value


def validate_pagination(page: int = 1, per_page: int = 10, max_per_page: int = 100) -> Dict[str, int]:
    """
    Validate pagination parameters.
    
    Args:
        page: Page number (1-indexed)
        per_page: Items per page
        max_per_page: Maximum items per page
        
    Returns:
        Dictionary with validated pagination parameters
        
    Raises:
        ValueError: If parameters are invalid
    """
    if page < 1:
        raise ValueError("page must be at least 1")
    if per_page < 1:
        raise ValueError("per_page must be at least 1")
    if per_page > max_per_page:
        raise ValueError(f"per_page cannot exceed {max_per_page}")
    
    return {
        "page": page,
        "per_page": per_page,
        "offset": (page - 1) * per_page
    }
