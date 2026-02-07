# Project Guidelines for func_adl_xAOD

## Code Style

- **Linter**: flake8 (ignores E501 line length and W503 line breaks)
- **Formatter**: black for code cleanup
- **Python**: 3.9+ compatible code required
- **Pattern**: Functional programming style—no statements/flow control in Python expressions (no `if`/`while` loops in query code)

Key files exemplifying patterns:

- [func_adl_xAOD/atlas/xaod/query_ast_visitor.py](func_adl_xAOD/atlas/xaod/query_ast_visitor.py) - AST visitor pattern
- [func_adl_xAOD/common/cpp_representation.py](func_adl_xAOD/common/cpp_representation.py) - C++ representation classes

## Architecture

This is a query-to-C++ transpiler for ATLAS xAOD and CMS data analysis. The main flow:

1. **Input**: Python AST from `func_adl` library representing a functional query
2. **Processing**: `query_ast_visitor` (experiment-specific) traverses AST and emits C++ representations
3. **Output**: Generated C++ files ready to compile and run on ROOT data files

**Core Components**:

- `common/`: ~80% of code—AST translation, type system, scope/statement tracking, code emission
- `atlas/xaod/`: ATLAS-specific event collection access, metadata handling
- `cms/{aod,miniaod}/`: CMS-specific implementations
- `template/`: Docker-based template scaffolding for compilation and execution

**Key Design Patterns**:

- **AST Visitor**: `ast.NodeVisitor` subclass iterates tree, caches results on `node.rep`
- **Scope Management**: `gc_scope` tracks variable visibility across nested blocks (loops, conditionals)
- **Type System**: `terminal` (primitives), `collection` (iterable), `tuple`/`dict` (non-C++ containers), `cpp_sequence` (iterators)
- **Code Accumulation**: `generated_code` object holds statements, variables, includes; emits via `add_line()`
- **Metadata Injection**: Special `Metadata` calls augment code generation behavior (type hints, dependencies)

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed descriptions of type system, statements, and scope handling.

## Build and Test

**Install**:

If doing build testing, create a local virtual environment. Prefer `uv`:
`uv venv --python=3.13`.

```bash
uv pip install -e .[test]           # Core + test dependencies
uv pip install -e .[test,local]     # + Docker support for integration tests
```

Activate the virtual environment.

If running on windows, the rust and MSVC tools may need to be installed. Tell the user to run the following commands (they must do it because it will require elevation):

```powershell
winget install Rustlang.Rustup
winget install Microsoft.VisualStudio.2022.BuildTools
```

Invoke the installer for BuildTools, and select C++ desktop tools, and the standalone package for arm64 for msvc v143

**Test Commands**:

- `pytest` - Run all unit tests (fastest, no Docker required)
- `pytest -m "atlas_xaod_runner"` - ATLAS R21 integration tests (requires Docker)
- `pytest -m "atlas_r22_xaod_runner"` - ATLAS R22 integration tests
- `pytest -m "cms_aod_runner"` - CMS AOD integration tests
- `pytest -m "cms_miniaod_runner"` - CMS miniAOD integration tests
- Coverage: `pytest --cov=func_adl_xAOD --cov-report=xml`

**Key Test Patterns** (see [tests/conftest.py](tests/conftest.py)):

- Fixtures auto-clear global type info (`g_method_type_dict`, `g_toplevel_ns`) between tests
- AsyncIO event loop fixture for async test support
- Test structure mirrors source: `tests/atlas/xaod/test_*.py` matches `func_adl_xAOD/atlas/xaod/*.py`

## Project Conventions

### Type Handling

**Do not use Python's `math.sin()`—use bare `sin()`** in expressions. The translator maps Python function names to C++ equivalents without namespace prefixes. See `func_adl_xAOD/common/cpp_functions.py` for mappings.

### Metadata Specification

Queries can inject metadata to guide C++ generation:

```python
Metadata({
    "metadata_type": "add_method_type_info",
    "type_string": "xAOD::Jet",
    "method_name": "pT",
    "return_type": "float"
})
```

Prevent circular dependencies; no two metadata blocks with same name and different content.

### Variable Scope Declaration

Use scope services to declare variables at correct nesting levels. Example: `Count` predicates must declare counters *outside* the jet loop scope, not inside. The `gc_scope` object provides methods to walk up/down the scope stack.

### Language Limitations

- **Supported**: Function calls, lambdas, property access, binary/unary/comparison ops, integer indexing, tuple/list output
- **Not supported**: `if`/`while`/`for` statements, assignment, `append()` (mutations), multi-arg comparisons (e.g., `a > b > c`)
- Use functional predicates: `Select`, `SelectMany`, `Where`, `First`, `Aggregate`, `Count`, `Sum`, `Min`, `Max`

### C++ Keywords and Include Tracking

Function mappings in `cpp_functions.py` track C++ names, return types, and required includes. New C++ functions added to events must specify their code-behind in `event_collections.py` for each backend.

## Integration Points

- **func_adl**: Upstream library providing AST and LINQ predicate definitions
- **qastle**: Query language (AST input)
- **ROOT**: Data file format and TTree output
- **Jinja2**: Template rendering for C++ code scaffolding
- **requests/retry**: Used for external service calls
- **Docker**: Integration test execution (optional; required for `_runner` tests)

## Security

No sensitive credentials in code. Version management via `func_adl_xAOD/version.txt` (read by hatchling). PyPI publishing triggered only on GitHub releases (see `.github/workflows/pypi.yaml`).
