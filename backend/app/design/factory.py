from app.design.mock import MockDesignGenerator


def get_design_generator():
    # Provider selection stays behind this boundary.
    # A future AI/optimization generator can replace the mock implementation.
    return MockDesignGenerator()
