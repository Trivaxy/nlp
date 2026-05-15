nlp (No Llama.Cpp) is a CLI wrapper for llama.cpp binaries that gets out of your way.

It:
1. Downloads, builds, and manages llama.cpp versions for you
2. Lets you manage where your models are stored, as `nlp` does not dictate anything
3. Lets you create and save profiles to avoid shell script spam for launching models

## Install

```
uv tool install nlp
```

Or from source:

```
git clone https://github.com/Trivaxy/nlp && cd nlp
uv sync
```

## Quick Start

```
nlp update                           # fetch, build, install latest
nlp use latest                       # activate the newly built version

nlp model register gemma /path/to/gemma4-31b.gguf
nlp profile create developer --model gemma --system-prompt "Make no mistakes" --args "--temp 1.0 --ctx-size 4096"

nlp cli developer                    # run llama-cli with the 'developer' profile
nlp server developer                 # or run llama-server instead
```

## Version Management

nlp manages different llama.cpp installations.

```
nlp update                           # build and install the latest release
nlp install b9145                    # install a specific version
nlp install b9145 --backends cuda    # install with specific backends
nlp use b9145                        # switch active version
nlp use latest                       # switch to the latest built version
nlp use b9145 --auto-install         # install first, then switch
nlp list                             # list installed versions
nlp uninstall b9145                  # uninstall a version
```

Backends are comma-separated (`cuda,vulkan,cpu`). If omitted, nlp tries to auto-detect the best backends for your system.

## Model Management

```
nlp model register my-model ~/models/qwen-3.6-27b-q4_k_m.gguf
nlp model unregister my-model
nlp model list
```

## Profile Management

A profile specifies a model, optional system prompt, and optional extra arguments.

```
nlp profile create my-profile --model my-model
nlp profile create my-profile --model my-model --args "--temp 0.7 --ctx-size 4096"
nlp profile create my-profile --model my-model --system-prompt "You are a cat."
nlp profile show my-profile
nlp profile delete my-profile
nlp profile list
nlp profile edit  # open config in $EDITOR
```

Config file lives at `~/.config/nlp/config.toml` (overridable via the `NLP_CONFIG_DIR` environment variable).

## Running Binaries

Every llama.cpp binary is aliased as a subcommand. Run `nlp --help` for the full list.

```
nlp cli default
nlp server default
nlp bench default
nlp embedding default
nlp quantize default
nlp tokenize default
nlp gguf default
nlp perplexity default
nlp imatrix default
nlp finetune default
nlp speculative default
nlp parallel default
... and the rest, too many to count
```

Extra args get passed as-is to the underlying llama.cpp executable. In case of conflicts with the profile's arguments, the extra args get used instead:

```
nlp cli default --temp 0.5 -n 256
```

## Running Test Binaries

```
nlp test chat default
nlp test grammar-parser default
nlp test sampling default
nlp test backend-ops default
nlp test tokenizer-0 default
...
```

Run `nlp test --help` for the full list of available tests.

## Development

```
git clone https://github.com/Trivaxy/nlp && cd nlp
uv sync --extra dev
uv run pytest -v
```
