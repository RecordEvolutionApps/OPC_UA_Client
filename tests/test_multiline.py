#!/usr/bin/env python3
"""
Test script to verify multiline YAML environment variable handling.
Tests the clean_multiline_env_var function with various input formats.
"""

import json

def clean_multiline_env_var(env_value):
    """
    Clean multiline YAML strings that come from environment variables.
    Handles escaped newlines (\n) and actual newlines, strips extra whitespace.
    """
    if not env_value:
        return env_value
    
    # Replace literal \n strings with actual newlines
    cleaned = env_value.replace('\\n', '\n')
    
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in cleaned.split('\n')]
    
    # Join back together, removing empty lines
    cleaned = ''.join(line for line in lines if line)
    
    return cleaned


def test_multiline_parsing():
    """Test various multiline input formats."""
    
    # Test 1: Compact single-line format
    test1 = '[{"NodeClass":"Variable","NodeId":"ns=2;s=Tank.Temperature","BrowseName":"Temperature"}]'
    result1 = clean_multiline_env_var(test1)
    parsed1 = json.loads(result1)
    print("✓ Test 1 passed: Compact single-line format")
    print(f"  Input length: {len(test1)}, Output length: {len(result1)}")
    print(f"  Parsed: {parsed1[0]['BrowseName']}")
    print()
    
    # Test 2: Multiline with actual newlines (from YAML pipe |)
    test2 = """[
  {
    "NodeClass": "Variable",
    "NodeId": "ns=2;s=Tank.Temperature",
    "BrowseName": "Temperature"
  }
]"""
    result2 = clean_multiline_env_var(test2)
    parsed2 = json.loads(result2)
    print("✓ Test 2 passed: Multiline with actual newlines")
    print(f"  Input length: {len(test2)}, Output length: {len(result2)}")
    print(f"  Parsed: {parsed2[0]['BrowseName']}")
    print()
    
    # Test 3: Escaped newlines (from shell export)
    test3 = '[\\n  {\\n    "NodeClass": "Variable",\\n    "NodeId": "ns=2;s=Tank.Temperature",\\n    "BrowseName": "Temperature"\\n  }\\n]'
    result3 = clean_multiline_env_var(test3)
    parsed3 = json.loads(result3)
    print("✓ Test 3 passed: Escaped newlines")
    print(f"  Input length: {len(test3)}, Output length: {len(result3)}")
    print(f"  Parsed: {parsed3[0]['BrowseName']}")
    print()
    
    # Test 4: Legacy schema format with newlines
    test4 = """{
  "Tank": "Temperature",
  "Machine": {
    "Status": "Voltage"
  }
}"""
    result4 = clean_multiline_env_var(test4)
    parsed4 = json.loads(result4)
    print("✓ Test 4 passed: Legacy schema with newlines")
    print(f"  Input length: {len(test4)}, Output length: {len(result4)}")
    print(f"  Parsed keys: {list(parsed4.keys())}")
    print()
    
    # Test 5: Multiple nodes with complex formatting
    test5 = """[
  {
    "NodeClass": "Variable",
    "NodeId": "ns=2;s=Tank.Temperature",
    "BrowseName": "Temperature",
    "DisplayName": "Tank Temperature"
  },
  {
    "NodeClass": "Variable",
    "NodeId": "ns=2;s=Machine.Voltage",
    "BrowseName": "Voltage"
  }
]"""
    result5 = clean_multiline_env_var(test5)
    parsed5 = json.loads(result5)
    print("✓ Test 5 passed: Multiple nodes")
    print(f"  Input length: {len(test5)}, Output length: {len(result5)}")
    print(f"  Parsed {len(parsed5)} nodes: {[n['BrowseName'] for n in parsed5]}")
    print()
    
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    test_multiline_parsing()
