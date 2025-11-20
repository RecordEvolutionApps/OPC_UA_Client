#!/usr/bin/env python3
"""
Tests for flatTree JSON to table conversion
"""

import unittest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flatTree import json_tree_to_table, flatten_json_tree


class TestFlatTree(unittest.TestCase):
    """Test flatTree conversion functions"""
    
    def test_flatten_simple_flat_structure(self):
        """Test flattening a simple flat structure"""
        json_obj = {
            "Temperature": 42.5,
            "Pressure": 2.1
        }
        tsp = "2025-11-20T10:00:00Z"
        
        rows = flatten_json_tree(json_obj, tsp)
        
        self.assertEqual(len(rows), 2)
        self.assertIn({"tsp": tsp, "variable": "Temperature", "value": 42.5}, rows)
        self.assertIn({"tsp": tsp, "variable": "Pressure", "value": 2.1}, rows)
    
    def test_flatten_nested_structure(self):
        """Test flattening a nested structure"""
        json_obj = {
            "Machine1": {
                "Tank": {
                    "Temperature": 65.3,
                    "Pressure": 2.5
                }
            }
        }
        tsp = "2025-11-20T10:00:00Z"
        
        rows = flatten_json_tree(json_obj, tsp)
        
        self.assertEqual(len(rows), 2)
        self.assertIn({
            "tsp": tsp,
            "variable": "Machine1.Tank.Temperature",
            "value": 65.3
        }, rows)
        self.assertIn({
            "tsp": tsp,
            "variable": "Machine1.Tank.Pressure",
            "value": 2.5
        }, rows)
    
    def test_flatten_mixed_depth(self):
        """Test flattening structure with mixed depths"""
        json_obj = {
            "Status": "Running",
            "Machine1": {
                "Tank": {
                    "Temperature": 65.3
                }
            }
        }
        tsp = "2025-11-20T10:00:00Z"
        
        rows = flatten_json_tree(json_obj, tsp)
        
        self.assertEqual(len(rows), 2)
        self.assertIn({"tsp": tsp, "variable": "Status", "value": "Running"}, rows)
        self.assertIn({
            "tsp": tsp,
            "variable": "Machine1.Tank.Temperature",
            "value": 65.3
        }, rows)
    
    def test_json_tree_to_table(self):
        """Test complete json_tree_to_table conversion"""
        json_obj = {
            "tsp": "2025-11-20T10:00:00Z",
            "data": {
                "Machine1": {
                    "Tank": {
                        "Temperature": 65.3
                    }
                }
            }
        }
        
        rows = json_tree_to_table(json_obj)
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["tsp"], "2025-11-20T10:00:00Z")
        self.assertEqual(rows[0]["variable"], "Machine1.Tank.Temperature")
        self.assertEqual(rows[0]["value"], 65.3)
    
    def test_json_tree_to_table_auto_timestamp(self):
        """Test that json_tree_to_table generates timestamp if missing"""
        json_obj = {
            "data": {
                "Temperature": 42.5
            }
        }
        
        rows = json_tree_to_table(json_obj)
        
        self.assertEqual(len(rows), 1)
        self.assertIn("tsp", rows[0])
        self.assertEqual(rows[0]["variable"], "Temperature")
        self.assertEqual(rows[0]["value"], 42.5)
    
    def test_flatten_skips_tsp_field(self):
        """Test that 'tsp' field is not included as a variable"""
        json_obj = {
            "tsp": "2025-11-20T10:00:00Z",
            "Temperature": 42.5
        }
        tsp = "2025-11-20T10:00:00Z"
        
        rows = flatten_json_tree(json_obj, tsp)
        
        # Should only have Temperature, not tsp
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["variable"], "Temperature")
    
    def test_flatten_with_string_values(self):
        """Test flattening with string values"""
        json_obj = {
            "Status": "Running",
            "Mode": "Auto"
        }
        tsp = "2025-11-20T10:00:00Z"
        
        rows = flatten_json_tree(json_obj, tsp)
        
        self.assertEqual(len(rows), 2)
        self.assertIn({"tsp": tsp, "variable": "Status", "value": "Running"}, rows)
        self.assertIn({"tsp": tsp, "variable": "Mode", "value": "Auto"}, rows)
    
    def test_flatten_with_numeric_types(self):
        """Test flattening with various numeric types"""
        json_obj = {
            "IntValue": 42,
            "FloatValue": 3.14,
            "BoolValue": True
        }
        tsp = "2025-11-20T10:00:00Z"
        
        rows = flatten_json_tree(json_obj, tsp)
        
        self.assertEqual(len(rows), 3)
        # Check that values are preserved with correct types
        values_by_var = {r["variable"]: r["value"] for r in rows}
        self.assertEqual(values_by_var["IntValue"], 42)
        self.assertAlmostEqual(values_by_var["FloatValue"], 3.14)
        self.assertEqual(values_by_var["BoolValue"], True)


if __name__ == '__main__':
    unittest.main()
