# sga_readiness

SGA readiness assessment tool.

## Requirements

- Python 3.12+

## Setup

```bash
pip install hatch
```

## Development

```bash
# Start a shell in the Hatch environment
hatch shell

# Run tests
hatch test

# Build the package
hatch build
```

## Usage

Create a `readiness.yaml` config file:

```yaml
checks:
  - name: "API health"
    type: http
    url: "http://localhost:8080/health"
    expected_status: 200

  - name: "Database reachable"
    type: port
    host: "localhost"
    port: 5432
    timeout: 5

  - name: "Redis"
    type: dependency
    host: "localhost"
    port: 6379
    timeout: 3

  - name: "API_KEY configured"
    type: config
    env_var: "API_KEY"
```

Run the checks:

```bash
# Text output
sga-readiness check --config readiness.yaml

# Verbose output with timing
sga-readiness check --config readiness.yaml --verbose

# JSON output
sga-readiness check --config readiness.yaml --format json
```

Or use as a library:

```python
from sga_readiness import run_checks

report = run_checks("readiness.yaml")
print(report.summary())  # "READY — 4 checks, 4 passed"
print(report.passed)     # True / False
```

### Check Types

| Type | Description | Required Fields |
|------|-------------|-----------------|
| `http` | GET a URL, validate status code / body | `url`, optional `expected_status`, `body_pattern` |
| `port` | TCP connectivity check | `host`, `port`, optional `timeout` |
| `config` | Env var or config file validation | `env_var` or `file_path`, optional `expected_value`, `file_pattern` |
| `dependency` | Port check + optional HTTP health | `host`, `port`, optional `health_url`, `timeout` |

## Project Structure

```
src/
  sga_readiness/       # Main source code
tests/                 # Test files
pyproject.toml         # Project config & dependencies
```

## License

`sga-readiness` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
