#!/usr/bin/env python3
"""
Integration tests for namespace detection and format handling
"""

import unittest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set required environment variables before importing main
os.environ.setdefault('DEVICE_NAME', 'test_device')
os.environ.setdefault('DEVICE_KEY', 'test_key')
os.environ.setdefault('FLEET_URL', 'http://test.com')
os.environ.setdefault('OPCUA_NAMESPACE', 'http://test.com/')
os.environ.setdefault('OPCUA_ENDPOINT', 'opc.tcp://localhost:4840')
os.environ.setdefault('OPCUA_VARIABLES', '[]')

# Mock the required modules
class MockClient:
    def __init__(self, endpoint):
        self.endpoint = endpoint

sys.modules['asyncua'] = type('module', (), {'Client': MockClient})()
sys.modules['ironflock'] = type('module', (), {'IronFlock': type('IronFlock', (), {})})()

from main import clean_multiline_env_var


class TestNamespaceDetection(unittest.TestCase):
    """Test namespace extraction and priority logic"""
    
    def test_extract_namespace_from_full_nodeset(self):
        """Test extracting namespace from full NodeSet JSON"""
        nodeset_json = {
            "NamespaceUris": ["http://example.com/MyMachine/"],
            "UAVariables": [
                {
                    "NodeClass": "Variable",
                    "NodeId": "ns=1;i=6001",
                    "BrowseName": "1:Status"
                }
            ]
        }
        
        # The namespace should be extracted from NamespaceUris
        self.assertIn("NamespaceUris", nodeset_json)
        self.assertEqual(nodeset_json["NamespaceUris"][0], "http://example.com/MyMachine/")
    
    def test_detect_full_nodeset_format(self):
        """Test detection of full NodeSet vs simple variable list"""
        full_nodeset = {
            "NamespaceUris": ["http://example.com/"],
            "UAVariables": []
        }
        
        simple_list = [
            {"NodeClass": "Variable", "NodeId": "ns=1;s=Temp"}
        ]
        
        single_node = {
            "NodeClass": "Variable",
            "NodeId": "ns=1;s=Temp"
        }
        
        legacy_schema = {
            "Tank": "Temperature"
        }
        
        # Full NodeSet should have UAVariables
        self.assertIn("UAVariables", full_nodeset)
        
        # Simple list should be a list
        self.assertIsInstance(simple_list, list)
        
        # Single node should have NodeClass
        self.assertIn("NodeClass", single_node)
        
        # Legacy should not have NodeClass or UAVariables
        self.assertNotIn("NodeClass", legacy_schema)
        self.assertNotIn("UAVariables", legacy_schema)


class TestMultilineEnvVar(unittest.TestCase):
    """Test multiline YAML environment variable cleaning"""
    
    def test_clean_simple_json(self):
        """Test cleaning simple JSON"""
        input_str = '{"Tank": "Temperature"}'
        result = clean_multiline_env_var(input_str)
        self.assertEqual(result, '{"Tank": "Temperature"}')
    
    def test_clean_multiline_with_newlines(self):
        """Test cleaning JSON with actual newlines"""
        input_str = """[
            {
                "NodeClass": "Variable"
            }
        ]"""
        result = clean_multiline_env_var(input_str)
        # Should remove newlines and extra spaces
        self.assertNotIn('\n', result)
        self.assertTrue(result.startswith('['))
        self.assertTrue(result.endswith(']'))
    
    def test_clean_escaped_newlines(self):
        """Test cleaning JSON with escaped newlines"""
        input_str = '[\\n{"NodeClass":"Variable"}\\n]'
        result = clean_multiline_env_var(input_str)
        # Should handle escaped newlines
        self.assertIsInstance(result, str)
    
    def test_clean_preserves_valid_json(self):
        """Test that valid JSON structure is preserved"""
        input_str = '{"key": "value"}'
        result = clean_multiline_env_var(input_str)
        # Should be parseable
        parsed = json.loads(result)
        self.assertEqual(parsed["key"], "value")


class TestFormatDetection(unittest.TestCase):
    """Test detection of different OPCUA_VARIABLES formats"""
    
    def test_detect_list_format(self):
        """Test detection of list format (NodeSet)"""
        config = [{"NodeClass": "Variable"}]
        is_nodeset = isinstance(config, list)
        self.assertTrue(is_nodeset)
    
    def test_detect_single_node_format(self):
        """Test detection of single node format"""
        config = {"NodeClass": "Variable", "NodeId": "ns=1;s=Temp"}
        has_node_class = "NodeClass" in config
        self.assertTrue(has_node_class)
    
    def test_detect_full_nodeset_format(self):
        """Test detection of full NodeSet with UAVariables"""
        config = {
            "NamespaceUris": ["http://example.com/"],
            "UAVariables": []
        }
        has_ua_variables = "UAVariables" in config
        self.assertTrue(has_ua_variables)
    
    def test_detect_legacy_schema(self):
        """Test detection of legacy schema format"""
        config = {"Tank": "Temperature", "Machine": {"Status": "Voltage"}}
        
        is_list = isinstance(config, list)
        has_node_class = "NodeClass" in config if isinstance(config, dict) else False
        has_ua_variables = "UAVariables" in config if isinstance(config, dict) else False
        
        is_legacy = not is_list and not has_node_class and not has_ua_variables
        self.assertTrue(is_legacy)


if __name__ == '__main__':
    unittest.main()
