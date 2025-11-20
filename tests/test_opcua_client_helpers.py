#!/usr/bin/env python3
"""
Unit tests for OPCUAClient helper functions
Tests namespace extraction, NodeId parsing, and nested dict operations
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the asyncua module before importing OPCUAClient
class MockClient:
    def __init__(self, endpoint):
        self.endpoint = endpoint

sys.modules['asyncua'] = type('module', (), {'Client': MockClient})()

from OPCUAClient import OPCUAClient


class TestOPCUAClientHelpers(unittest.TestCase):
    """Test helper methods in OPCUAClient"""
    
    def setUp(self):
        """Set up test client"""
        self.client = OPCUAClient("opc.tcp://localhost:4840", "http://example.com/")
    
    def test_parse_nodeid_string_format(self):
        """Test parsing string-based NodeId"""
        # String identifier
        ns, identifier = self.client._parse_nodeid("ns=1;s=Machine1.Tank.Temperature")
        self.assertEqual(ns, 1)
        self.assertEqual(identifier, "Machine1.Tank.Temperature")
        
        # Integer identifier
        ns, identifier = self.client._parse_nodeid("ns=2;i=1001")
        self.assertEqual(ns, 2)
        self.assertEqual(identifier, "1001")
        
        # Default namespace
        ns, identifier = self.client._parse_nodeid("ns=0;s=Root")
        self.assertEqual(ns, 0)
        self.assertEqual(identifier, "Root")
    
    def test_parse_nodeid_dict_format(self):
        """Test parsing dict-based NodeId"""
        nodeid_dict = {
            "IdType": "String",
            "Id": "Machine1.Tank.Temperature",
            "Namespace": 2
        }
        ns, identifier = self.client._parse_nodeid(nodeid_dict)
        self.assertEqual(ns, 2)
        self.assertEqual(identifier, "Machine1.Tank.Temperature")
    
    def test_extract_namespace_from_nodeset(self):
        """Test extracting namespace URI from NodeSet"""
        # Full NodeSet with NamespaceUris
        nodeset = {
            "NamespaceUris": ["http://example.com/MyMachine/"],
            "UAVariables": []
        }
        namespace = self.client._extract_namespace_from_nodeset(nodeset)
        self.assertEqual(namespace, "http://example.com/MyMachine/")
        
        # No NamespaceUris
        nodeset_no_ns = {"UAVariables": []}
        namespace = self.client._extract_namespace_from_nodeset(nodeset_no_ns)
        self.assertIsNone(namespace)
        
        # List format (no namespace)
        nodeset_list = [{"NodeClass": "Variable"}]
        namespace = self.client._extract_namespace_from_nodeset(nodeset_list)
        self.assertIsNone(namespace)
    
    def test_build_nested_dict_single_level(self):
        """Test building nested dict with single level"""
        result = self.client._build_nested_dict(["Temperature"], 42.5)
        self.assertEqual(result, {"Temperature": 42.5})
    
    def test_build_nested_dict_multi_level(self):
        """Test building nested dict with multiple levels"""
        result = self.client._build_nested_dict(["Machine1", "Tank", "Temperature"], 65.3)
        expected = {"Machine1": {"Tank": {"Temperature": 65.3}}}
        self.assertEqual(result, expected)
    
    def test_merge_nested_dicts_simple(self):
        """Test merging two simple nested dicts"""
        dict1 = {"Machine1": {"Tank": {"Temperature": 65.3}}}
        dict2 = {"Machine1": {"Tank": {"Pressure": 2.5}}}
        
        result = self.client._merge_nested_dicts(dict1, dict2)
        expected = {
            "Machine1": {
                "Tank": {
                    "Temperature": 65.3,
                    "Pressure": 2.5
                }
            }
        }
        self.assertEqual(result, expected)
    
    def test_merge_nested_dicts_different_branches(self):
        """Test merging dicts with different branches"""
        dict1 = {"Machine1": {"Tank": {"Temperature": 65.3}}}
        dict2 = {"Machine1": {"Motor": {"Speed": 1450.0}}}
        
        result = self.client._merge_nested_dicts(dict1, dict2)
        expected = {
            "Machine1": {
                "Tank": {"Temperature": 65.3},
                "Motor": {"Speed": 1450.0}
            }
        }
        self.assertEqual(result, expected)
    
    def test_merge_nested_dicts_overwrite(self):
        """Test that merge overwrites non-dict values"""
        dict1 = {"status": "old"}
        dict2 = {"status": "new"}
        
        result = self.client._merge_nested_dicts(dict1, dict2)
        self.assertEqual(result, {"status": "new"})


if __name__ == '__main__':
    unittest.main()
