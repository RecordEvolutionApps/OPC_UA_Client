## Testing

The project includes comprehensive unit and integration tests covering:
- OPCUAClient helper methods (NodeId parsing, namespace extraction, nested dict operations)
- flatTree conversion functions
- Namespace detection and format handling

Run all tests:
```bash
python3 tests/test_opcua_client_helpers.py
python3 tests/test_flattree_unit.py
python3 tests/test_namespace_and_formats.py
```

Demo scripts showing format capabilities:
```bash
python3 tests/demo_flat_vs_nested.py
python3 tests/demo_nested_logic.py
python3 tests/demo_nested_extraction.py
```

---