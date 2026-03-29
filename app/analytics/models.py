class ValidationResult:
    """Standard model for all validation rule results."""
    def __init__(self, is_valid: bool, error_type: str = None, message: str = None):
        self.is_valid = is_valid
        self.error_type = error_type
        self.message = message
