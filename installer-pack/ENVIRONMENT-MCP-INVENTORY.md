# Environment and MCP inventory

This inventory is deliberately auditable and contains no secret values. It describes what the package can
use, what is optional, and what is intentionally not bundled. The supported baseline is Windows 10/11.

## Compatibility statuses

- `ready`: prompt/workflow skill works without an extra local runtime; live information still needs an available source.
- `requires-runtime`: needs a separately installed interpreter, CLI, or Python package.
- `requires-mcp`: needs a separately configured MCP server.
- `requires-credential`: needs a user-supplied endpoint/API key; the package never reads hidden config files.
- `unsupported/disabled`: retained as an explanation only; no compatible automatic entry point is shipped.

## Windows baseline

| Component | Status | Detection | Offline installer/package | Used by |
|---|---|---|---|---|
| Windows 10/11 x64 | must-package | `Get-CimInstance Win32_OperatingSystem` | supplied by Microsoft, not bundled | all |
| PowerShell 5.1+ | must-package | `$PSVersionTable.PSVersion` | supplied by Windows | installer and safe file operations |
| Python 3.10+ | optional | `python --version` or `py -3 --version` | `python-3.x.x-amd64.exe` | data, document, media and local database skills |
| Node.js 18+ | optional | `node --version` | `node-v18+-x64.msi` | only skills that add a Node workflow later |
| Git | optional | `git --version` | `Git-*-64-bit.exe` | repository deployment and versioning |
| curl.exe | optional Windows component | `Get-Command curl.exe` | Windows component | weather and simple HTTP checks |
| Browser driver | unsupported by default | explicit user check | not bundled | no default skill |

The installer does not download or silently install these components. Use the offline filename column as a
packaging checklist, verify the publisher/license, then install with the organization's approved procedure.

## Python packages

| Package | Status | Minimum | Detection | Used by |
|---|---|---:|---|---|
| `pandas` | optional | current supported release | `python -c "import pandas"` | stock/fund/macro/venture/wealth/data |
| `numpy` | optional | current supported release | `python -c "import numpy"` | analysis and finance |
| `matplotlib` | optional | current supported release | `python -c "import matplotlib"` | charts and finance |
| `akshare` | optional | current supported release | `python -c "import akshare"` | A 股 and funds |
| `openpyxl` | optional | current supported release | `python -c "import openpyxl"` | Excel |
| `python-docx` | optional | current supported release | `python -c "import docx"` | Word |
| `python-pptx` | optional | current supported release | `python -c "import pptx"` | PowerPoint |
| `pypdf` | optional | current supported release | `python -c "import pypdf"` | PDF |
| `pdfplumber` | optional | current supported release | `python -c "import pdfplumber"` | PDF/table extraction |
| `reportlab` | optional | current supported release | `python -c "import reportlab"` | PDF/document output |
| `scrapling[fetchers]` | optional | current supported release | `python -c "import scrapling"` | web content fallback |
| `html2text` | optional | current supported release | `python -c "import html2text"` | web content fallback |

Exact versions are intentionally not frozen here because a clean offline deployment must supply and audit
its own wheelhouse. `dependencies.json` records the package names and the need for a runtime.

## MCP and credentials

| Server / credential | Status | Configuration | Related capabilities |
|---|---|---|---|
| Feishu MCP | 待配置 / `requires-mcp` | `manifest/feishu.template.json` | four Feishu skills |
| DashScope web search | optional / `requires-credential` | `manifest/dashscope-web-search.template.env` | web search extraction |
| Image service endpoint | optional / `requires-credential` | `manifest/image-2.template.env` | image generation/edit |
| Video service endpoint | optional / `requires-credential` | `manifest/seedance.template.env` | video generation |
| API keys, tokens, cookies, private URLs | never package | local environment or secret manager only | external services |

No MCP server executable, private config, token, session history, memory database, cache, draft or generated
artifact is part of the public package. Health checks are described in `manifest/mcp-inventory.json`.

## Network policy

Network is optional for prompt-only work. Live search, weather, market data, document fetching and external
generation need network access and should state the source/date. Offline mode must fail clearly rather than
silently returning stale data.
