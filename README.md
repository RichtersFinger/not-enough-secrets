# not-enough-secrets

A small command line tool for file encryption.
It keeps a simple job simple: pick a file, get an encrypted file back.

The tool is built around pluggable modules, so the actual crypto is swappable and versioned, while the interface stays the same.
If a software component is not installed, modules report themselves as unavailable instead of breaking.

## Quick example

```bash
# encrypt a file, result goes to stdout by default
not-enough-secrets encrypt secret.txt -o secret.txt.nes

# decrypt it again
not-enough-secrets decrypt secret.txt.nes -o secret.txt

# encrypt in place, with a backup safety net and print output to stdout
not-enough-secrets encrypt --stdout --in-place secret.txt
```

You get prompted for the key on stdin.

## Install

From the Python Package Index:

```bash
pip install not-enough-secrets
```
or install with extra `cryptography` (enabling, for example, AES-GCM)
```bash
pip install not-enough-secrets[cryptography]
```

From a Debian package:
Download a release package and enter
```bash
dpkg -i not-enough-secrets_<version>.deb
```

## Usage

The tool has four commands: `version`, `modules`, `encrypt` and `decrypt`.

List modules:

```bash
# only modules that are available on your system
not-enough-secrets modules
# also show modules you cannot use, but with their requirements
not-enough-secrets modules --all
```

Encrypt and decrypt share the same output options:

- default writes the result to stdout
- `-o, --output PATH` writes to a file, add `-f, --force` to overwrite an existing one
- `--in-place` replaces the input file, and only does so once the new content is safely written
- `--stdout` can be added alongside `-o` or `--in-place` to also print the result

Pick a module with `-m`.
The value is the module identifier, optionally followed by options after a colon (options are module specific):

```bash
not-enough-secrets encrypt notes.txt -m aes-gcm-0:128 -o notes.nes
```

Leave `-m` off and encrypt picks a sane default for your system.
Decrypt reads the module and its settings from the file header, so you normally only need to supply the key.
You can still pass `-m` on decrypt to force a specific module if you know what you are doing.

Add `-v` for info logging or `--debug` for debug logging and full tracebacks (logs to stderr).

### Modules

- `aes-gcm-0` AES-GCM with a PBKDF2-HMAC-SHA256 derived key. Optional key size of 128, 192 or 256 bits, default 256. Needs the `cryptography` package.
- `fernet-0` Fernet authenticated encryption with a PBKDF2-HMAC-SHA256 derived key. No options. Needs the `cryptography` package.
- `base64` Base64 obfuscation. This is not encryption and provides no security at all. It exists for tests and debugging, do not use it for real data.

Each module carries its own version in its identifier.
Older files keep working because the matching module version stays around to read them.

## Build

```
# placeholder: build the Python package
# placeholder: build the .deb
```

## Development

```
# placeholder: set up a dev environment
# placeholder: run the tests
```

## Future Additions

Without any specific order:

- **Streaming**: add support for encrypting/decrypting a stream
- **Detect**: add a `detect` command to identify a file (attempt to read and print file header)
- **Module id validation**: add validation of module id to be alphanumeric+"-" (maybe in registry on load)
- **Modules**:
  - system's open-ssl
  - ?
- **Options**:
  - option to skip key confirmation on encode
- **Tests**:
  - add fixtures for all modules (+their versions) to ensure backwards compatibility
- **Misc**:
  - fix missing newline when using `--stdout`
  - consider support a short-hand/convenience cli invocation (only base command, then decide whether encrypt/decrypt through file header analysis)
  - add prominent warning when running `base64mod`
