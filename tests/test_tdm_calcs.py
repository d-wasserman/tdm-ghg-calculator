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
            
    def test_t2_increase_job_density_strategy(self):
        """Test the job density strategy."""
        # Mock the input data
        proposed_job_density = 500
        typical_job_density = 145
        elasticity_vmt_job_density = -0.07        
        # Expected result based on the mock data
        expected_result = -0.171
        
        # Call the function under test
        result = tdm_ghg.mitigations.t2_increase_job_density(proposed_job_density, typical_job_density, elasticity_vmt_job_density)
        
        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), \
            f"Expected {expected_result}, but got {result}"
    def test_t3_provide_tod_strategy(self):
        """Test the tod strategy."""
        # Mock the input data
        transit_mode_share = 4
        ratio = 4.9
        auto_mode_share = -90        
        # Expected result based on the mock data
        expected_result = -0.272
        
        # Call the function under test
        result = tdm_ghg.mitigations.t3_provide_transit_oriented_development(transit_mode_share,ratio,auto_mode_share)
        
        # Assert that the result matches the expected output
        assert isclose(result, expected_result, rel_tol=1e-2), \
            f"Expected {expected_result}, but got {result}"


