# func_adl_xAOD

 Backend that converts `qastle` to run on an ATLAS xAOD backend.

[![GitHub Actions Status](https://github.com/iris-hep/func_adl_xAOD/workflows/CI/CD/badge.svg)](https://github.com/iris-hep/func_adl_xAOD/actions?branch=master)
[![Code Coverage](https://codecov.io/gh/iris-hep/func_adl_xAOD/graph/badge.svg)](https://codecov.io/gh/iris-hep/func_adl_xAOD)

[![PyPI version](https://badge.fury.io/py/func-adl-xAOD.svg)](https://badge.fury.io/py/func-adl-xAOD)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/func-adl-xAOD.svg)](https://pypi.org/project/func-adl-xAOD/)

## Introduction

This allows you to query hierarchical data stored in a root file that has been written using the ATLAS xAOD format.
This code allows you to query that.

## Features

A short list of some of the features that are supported by the `xAOD` C++ translator follows.

### Python

Many, but not all, parts of the `python` language are supported. As a general rule, anything that is a statement or flow control is not supported. So no `if` or `while` or `for` statements, for example. Assignment isn't supported, which may sound limiting - but this is a functional implementation so it is less to than one might think.

What follows are the parts of the language that are covered:

- Function calls, method calls, property references, and lambda calls (and lambda functions), with some limitations.
- Integer indexing into arrays
- Limited tuple support as a means of collecting information together, or as an output to a ROOT file.
- Limited list support (in same way as above). In particular, the `append` method is not supported as that modifies the list, rather than creating a new one.
- Unary, Binary, and comparison operations. Only 2 argument comparisons are supported (e.g. `a > b` and not `a > b > c`).
- Using `and` and `or` to combine conditional expressions. Note that this is written as `&` and `|` when writing an expression due to the fact `python` demands a `bool` return from `and` and `or` when written in code.
- The conditional if expression (`10 if a > 10 else 20`)
- Floating point numbers, integers, and strings.

### xAOD Functions

You can call the functions that are supported by the C++ objects as long as the required arguments are primitive types. Listed below are special _extra_ functions attached to various objects in the ATLAS xAOD data model.

#### The Event

The event object has the following special functions to access collections:

- `Jets`, `Tracks`, `EventInfo`, `TruthParticles`, `Electrons`, `Muons`, and `MissingET`. Each function takes a single argument, the name of the bank in the xAOD. For example, for the electrons one can pass `"Electrons"`.

Adding new collections is fairly easy.

#### The Jet Object

Template functions don't make sense yet in python.

- `getAttribute` - this function is templated, so must be called as either `getAttributeFloat` or `getAttributeVectorFloat`.

### Math

- Math Operators: +, -, *, /, %, **
- Comparison Operators: <, <=, >, >=, ==, !=
- Unary Operators: +, -, not
- Math functions are pulled from the C++ [`cmath` library](http://www.cplusplus.com/reference/cmath/): `sin`, `cos`, `tan`, `acos`, `asin`, `atan`, `atan2`, `sinh`, `cosh`, `tanh`, `asinh`, `acosh`, `atanh`, `exp`, `ldexp`, `log`, `ln`, `log10`, `exp2`, `expm1`, `ilogb`, `log1p`, `log2`, `scalbn`, `scalbln`, `pow`, `sqrt`, `cbrt`, `hypot`, `erf`, `erfc`, `tgamma`, `lgamma`, `ceil`, `floor`, `fmod`, `trunc`, `round`, `rint`, `nearbyint`, `remainder`, `remquo`, `copysign`, `nan`, `nextafter`, `nexttoward`, `fdim`, `fmax`, `fmin`, `fabs`, `abs`, `fma`.
- Do not use `math.sin` in a call. However `sin` is just fine. If you do, you'll get an exception during resolution that it doesn't know how to translate `math`.
- for things like `sum`, `min`, `max`, etc., use the `Sum`, `Min`, `Max` LINQ predicates.

### Metadata

It is possible to inject metadata into the `qastle` query to alter the behavior of the C++ code production. Each sub-section below has a different type of metadata. In order to invoke this, use the `Metadata` call, which takes as input stream and outputs the same stream, but the argument is a dictionary which contains the metadata.

A few things about metadata:

- No two metadata blocks can have the same name and different content. However, it is legal for them to have different dependencies. In that case, the multiple blocks are treated as a single block with a union of the dependencies.
- Exceptions (`ValueError`) are raised if the dependency graph can't be completed, or a circular dependency is discovered.

#### Method Return Type

If you have a method that returns a non-standard type, use this metadata type to specify to the backend the return type. There are two different forms for this metadata - one if a single item is returned, and another if a collection of items are returned.

For a _single item_:

| Key | Description | Example |
| ------------ | ------------ | --------------|
| metadata_type | The metadata type | `"add_method_type_info"` |
| type_string | The object the method applies to, fully qualified, C++ | `"xAOD::Jet"` |
| method_name | Name of the method | `"pT"` |
| return_type | Type returned, C++, fully qualified | `"float"`, `"float*"`, `"float**"` |
| deref_count | Number of times to dereference object before invoking this method (optional) | 2 |

Note: `deref_count` is used when an object can "hide" hold onto other objects by dereferencing them (e.g. by overriding the operator `operator*`). If it is zero (as it mostly is since `operator*` isn't often overridden), then it can be omitted.

For a _collection_:

| Key | Description | Example |
| ------------ | ------------ | --------------|
| metadata_type | The metadata type | `"add_method_type_info"` |
| type_string | The object the method applies to, fully qualified, C++ | `"xAOD::Jet"` |
| method_name | Name of the method | `"jetWeights"` |
| return_type_element | The type of the collection element | `"float"` |
| return_type_collection | The type of the collection | `vector<float>`, `vector<float>*` |
| deref_count | Number of times to dereference object before invoking this method (optional) | 2 |

#### C++ Inline Functions and Methods

These are inline functions - they are placed inline in the code, surrounded by a braces. Only the `result` is declared
outside, and expected to be set somewhere inside the block. This mechanism can also specify a method. In that case
the optional parameter `instance_obj` should be specified.

| Key | Description | Example |
| ------------ | ------------ | --------------|
| metadata_type | The metadata type | `"add_cpp_function"` |
| name | C++ Function Name | `"DeltaR"` |
| include_files | List of include files | `[vector, TLorentzVector.h]` |
| arguments | List of argument names | `[vec1, vec2]` |
| code | List of code lines | `["auto t = (vec1+vec2);", "auto result = t.m();"]` |
| instance_object | Present only if this is an object replacement. It species the code string that should be replaced by the current object | `"xAOD::Jet_vt"` |
| method_object | The object name that the method can be called on. Present only if this is a method. | `"obj_j"` |
| result_name | If not using `result` what should be used (optional) | `"my_result"` |
| return_type | C++ return type | `double` |
| return_is_collection | If true, then the return is a collection of `return_type` | `True` |

Note that a very simple replacement is done for `result_name` - so it needs to be a totally unique name. The back-end may well change `result` to some other name (like `r232`) depending on the complexity of the expression being parsed.

If two functions are sent with the same name they must be identical or behavior is undefined.

#### Job Scripts

ATLAS runs job scripts to configure its environment. These are needed to do things like apply corrections, etc. This block allows those to be added on the fly. In ATLAS these jobs scripts are python.

| Key | Description | Example |
| ------------ | ------------ | --------------|
| metadata_type | The metadata type | `"add_job_script"` |
| name | Name of this script block | `"apply_corrections"` |
| script | List of lines of python | `["calibration = makeAnalysis('mc')", "job.addSequence(calibration)"]` |
| depends_on | List of other script blocks that this should come after | `["correction_setup"]` |

A dependency graph is built from the `depends_on` entry, otherwise the blocks will appear in a random order.

NOTE: Currently the CMS backend will ignore any job script metadata sent to it.

#### Event Level Collections

CMS and ATLAS store their basic reconstruction objects as collections (e.g. jets, etc.). You can define new collections on the fly with the following metadata

For _ATLAS_:

| Key | Description | Example |
| ------------ | ------------ | --------------|
| metadata_type | The metadata type | `"add_atlas_event_collection_info"` |
| name | The name of the collection (used to access it from the dataset object) | `"TruthParticles"` |
| include_files| List of include files to use when accessing collection | `['file1.h', 'file2.h']` |
| container_type | The container object that is filled | `"xAOD::ElectronContainer"` |
| element_type | The element in the container. In atlas this is a pointer. | `"xAOD::Electron"` |
| contains_collection | Some items are singletons (like `EventInfo`) | `True` or `False` |

For _CMS AOD_:

| Key | Description | Example |
| ------------ | ------------ | --------------|
| metadata_type | The metadata type | `"add_cms_aod_event_collection_info"` |
| name | The name of the collection (used to access it from the dataset object) | `"Vertex"` |
| include_files| List of include files to use when accessing collection | `['DataFormats/VertexReco/interface/Vertex.h']` |
| container_type | The container object that is filled | `"reco::VertexCollection"` |
| element_type | The element in the container. | `"reco::Vertex"` |
| contains_collection | Some items are singletons (like `EventInfo`) | `True` or `False` |
| element_pointer | Indicates if the element type is a pointer | `True` or `False` |

For _CMS miniAOD_:

| Key | Description | Example |
| ------------ | ------------ | --------------|
| metadata_type | The metadata type | `"add_cms_miniaod_event_collection_info"` |
| name | The name of the collection (used to access it from the dataset object) | `"Muon"` |
| include_files| List of include files to use when accessing collection | `[DataFormats/PatCandidates/interface/Muon.h]` |
| container_type | The container object that is filled | `"pat::MuonCollection"` |
| element_type | The element in the container. | `"pat::Muon"` |
| contains_collection | Some items are singletons (like `EventInfo`) | `True` or `False` |
| element_pointer | Indicates if the element type is a pointer | `True` or `False` |

#### Code Blocks

Code blocks provide a way to inject various lines of C++ into code. There are a number of options, and any combinations of keys can be used.

| Key | Description | Example |
| ------------ | ------------ | --------------|
| metadata_type | The metadata type | `"inject_code"` |
| name | The name of the code block | `"code_block_1"` |
| body_includes | List of files to include in the C++ file (`query.cpp`). | `["file1.hpp", "file2.hpp"]` |
| header_includes | List of files to include in the C++ header file (`query.hpp`). | `["file1.hpp", "file2.hpp"]` |
| private_members | List of class instance variables to declare (`query.hpp`) | `["int first;", "int second;"]` |
| instance_initialization | Initializers added to the constructor in the main C++ class file (`query.cpp`) | `["first(10)", "second(10)"]` |
| ctor_lines | Lines of C++ to add to the body of the constructor (`query.cpp`) | `["second = first * 10;"]`
| link_libraries | Items to add to the `CMake LINK_LIBRARIES` list (`CMakeLists.txt`) | `["TrigDecisionToolLib"]` |

A few things to note:

- Note the items that have semicolons and those that do not. This is crucial - the system will not add them in those cases!
- While the ordering of lines withing a single `inject_code` metadata block will be maintained, different blocks may be reordered arbitrarily.
- Include files always use the double-quote: `#include "file1.hpp"`
- The name of the code block is not used anywhere, and it must be unique. If two code blocks are submitted with the same name but different contents it will generate an error.

#### Docker Image

This metadata can only be used if you are running against a local file (e.g. using `xAODDataset` or similar). It allows you to configure which image you want to run against.

| Key | Description | Example |
| ------------ | ------------ | --------------|
| metadata_type | The metadata type | `"inject_code"` |
| image | The docker image and tag to run | `"atlas/analysisbase:21.2.195"` |

### Output Formats

The `xAOD` code only renders the `func_adl` expression as a ROOT file. The ROOT file contains a simple `TTree` in its root directory.

- If `AsROOTTTree` is the top level `func_adl` node, then the tree name and file name are taken from that expression. Only a sequence of python `tuples` or a single item can be understood by `AsROOTTTree`.
- If a `Select` sequence of `int` or `double` is the last `func_adl` expression, then a file called `xaod_output.root` will be generated, and it will contain a `TTree` called `atlas_xaod_tree` with a single column, called `col1`.
- If a `Select` sequence of a `tuple` is the last `func_adl` expression, then a file called `xaod_output.root` will be generated, and it will contain a `TTree` called `atlas_xaod_tree` with a columns named `col1`, `col2`, etc.
- If a `Select` sequence of dictionary's is the last `func_adl` expression, then a file called `xaod_output.root` will be generated, and it will contain a `TTree` called `atlas_xaod_tree`, with column names taken from the dictionary keys.

`ServiceX` (and the [`servicex` frontend package](https://pypi.org/project/servicex/)) can convert from ROOT to other formats like a `pandas.DataFrame` or an `awkward` array.

## Testing and Development

Setting up the development environment:

- After creating a virtual environment, do a setup-in-place: `pip install -e .[test]`

To run tests:

- `pytest -m "not atlas_xaod_runner and not cms_runner"` will run the _fast_ tests.
- `pytest -m "atlas_xaod_runner"`, `pytest -m "cms_aod_runner"` and `pytest -m "cms_miniaod_runner"`  will run the slow tests for ATLAS xAOD, CMS AOD and CMS miniAOD respectively that require docker installed on your command line. `docker` is involved via pythons `os.system` - so it needs to be available to the test runner.
- The CI on github is setup to run tests against python `3.7`, `3.8`, and `3.9` (only the non-xaod-runner tests).

Contributing:

- Develop in another repo or on a branch
- Submit a PR against the `master` branch.

In general, the `master` branch should pass all tests all the time. Releases are made by tagging on the master branch.

Publishing to PyPi:

- Automated by declaring a new release (or pre-release) in github's web interface

### Running Locally

Designed for running locally, it is possible to setup and use the `xAOD` backend if you have `docker` installed on your local machine. To use this you first need to install the local flavor of this package:

```bash
pip install func_adl_xAOD[local]
```

You can then use the `xAODDataset` object, the `CMSRun1AODDataset` object and `CMSRun2miniAODDataset` to execute `qastle` running on a docker image for ATLAS or CMS Run 1 AOD, locally.

- Specify the local path to files you want to run on in the arguments to the constructor
- Files are run serially, and in a blocking way
- This code is designed for development and testing work, and is not designed for large-scale production running on local files (not that that couldn't be done).

When something odd happens and you really want to look at the C++ output, you can do this by including the following code somewhere before the `xAOD` backend is executed. This will turn on logging that will dump the output from the run and will also dump the C++ header and source files that were used to execute the query.

```python
import logging
logging.basicConfig()
logging.getLogger("func_adl_xAOD.common.local_dataset").setLevel(level=logging.DEBUG)
```

- In general, the first two lines are a good thing to have in your notebooks, etc. It allows you to see where warning messages are coming from and might help when things are going sideways.

Note that some of the local runners will use a docker volume to cache calibration files and the like. If you need a truly fresh start, you'll need to remove the volume first.
