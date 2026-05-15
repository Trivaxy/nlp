nlp (No Llama.Cpp) is a CLI wrapper for llama.cpp binaries that gets out of your way.

It:
1. Automatically downloads, builds, and manages updates to your llama.cpp installation
2. Lets you manage where your models are stored. `nlp` does not dictate anything
3. Lets you create and save profiles, read more below

## Profiles

Profiles are what nlp launches. A profile is simply the model you want to use, parameters you want to pass to llama-cli/llama-server, and an optional system prompt.

## Install

```
uv tool install nlp
```

Or from source:

```
git clone https://github.com/Trivaxy/nlp && cd nlp
uv sync
```

## Quick start

Read this and you'll know everything about `nlp`.

This will fetch, build and install the latest llama.cpp version. Remember that llama.cpp updates several times a day.
```
nlp update
```

Now, we need a .gguf model. Suppose you have gemma4-31b on disk. `nlp` doesn't download or manage .gguf files for you, so instead you have to register them so that `nlp` knows they exist.
```
nlp model register gemma /path/to/gemma4-31b.gguf
```
`nlp` now knows that `gemma` points to `/path/to/gemma4-31b.gguf`.

We're almost there. When using llama.cpp, you often pass in tons of arguments. `nlp` encapsulates your choice of model as well as those arguments into a profile. So, we need to create one:
```
nlp profile create developer --model gemma --system-prompt "Make no mistakes" --args "--temp 1.0 --fit-ctx 64000"
```

Now you can run the profile.
```
nlp cli developer            # run llama-cli with the 'developer' profile
nlp server developer         # or run llama-server instead
```

If you want to edit profiles, you can run:
```
nlp profile edit
```

`nlp` also lets you invoke the other llama.cpp binaries directly. Read more below.

## Commands

### Managing models

```
nlp model register my-model ~/models/qwen-3.6-27b-q4_k_m.gguf
nlp model unregister my-model
nlp model list
```

### Managing profiles

A profile specifies a model and any extra arguments.

```
nlp profile create my-profile --model my-model
nlp profile create my-profile --model my-model --args "--temp 0.7 --ctx-size 4096"
nlp profile create my-profile --model my-model --system-prompt "You are a cat."
nlp profile show my-profile
nlp profile delete my-profile
nlp profile list
```

Profile config file lives at `~/.config/nlp/config.toml`. Edit it with:

```
nlp profile edit
```

### Running binaries

Every llama.cpp binary is aliased as a subcommand:

```
nlp server default           # llama-server
nlp bench default            # llama-bench
nlp embedding default        # llama-embedding
nlp quantize default         # llama-quantize
nlp tokenize default         # llama-tokenize
nlp perplexity default       # llama-perplexity
nlp gguf default             # llama-gguf
```

Extra args get forwarded to the binary:

```
nlp cli default --temp 0.5 -n 256
```

See `nlp --help` for the full list of aliases.

### Running test binaries

```
nlp test chat default
nlp test grammar-parser default
nlp test sampling default
```

## Updating

```
nlp update                   # build the latest release
nlp update --backend cpu     # force CPU-only build
nlp update --backend cuda    # force CUDA build
nlp update --backend vulkan  # force Vulkan build
```

Auto-update checks run on every command. Skip with `nlp -nu <command>`.

## Development

```
git clone https://github.com/YOUR_USER/nlp && cd nlp
uv sync --extra dev
uv run pytest -v
```
