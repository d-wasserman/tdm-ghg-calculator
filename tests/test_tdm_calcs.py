"""Unit tests for tdm-calcs library."""
import numpy as np
import pytest
from math import isclose
import tdm_ghg 

# ---- Constants ----

class TestMitigations:
    def test_t1_increase_residential_density_strategy(self):
        """Test the residential density strategy."""
        # Mock the input data
        proposed_residential_density = 16
        typical_residential_density = 9.1
        elasticity_vmt_residential_density = -0.22        
        # Expected result based on the mock data
        expected_result = -0.166
        
        # Call the function under test
        result = tdm_ghg.mitigations.t1_increase_residential_density(proposed_residential_density, typical_residential_density, elasticity_vmt_residential_density)
        
        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), \
            f"Expected {expected_result}, but got {result}"
            
        


