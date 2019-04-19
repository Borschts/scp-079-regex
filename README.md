# SCP-079-REGEX

This project is used to manage regular expression rules adopted by other bots. 
Not yet completed.

## How to use

See [this article](https://scp-079.org/regex/).

## Features

- Easy to use
- Can merge similar or mutually contained rules

## To Do List

- [x] Complete phrase management for a single group
- [x] Check the pattern before add
- [x] Choose the right way to store data
- [x] Interfacing with the whole project database
- [ ] Simplified Chinese to Traditional Chinese
- [ ] More groups

## Requirements

- Python 3.6 or higher.
- requirements.txt

## Files

- plugins
    - functions
        - `etc.py` : Miscellaneous
        - `files.py` : Save files
        - `telegram.py` : Some telegram functions
        - `words.py` : Manage words
    - handlers
        - `callback.py` : Handle callback
        - `commands` : Handle commands
    - `glovar.py` : Global variables
- `.gitignore` : Ignore
- `config.ini.example` -> `config.ini` : Configures
- `LICENSE` : GPLv3
- `main.py` : Start here
- `README.md` : This file
- `requirements.txt` : Managed by pip

## Contribute

Welcome to make this project even better. You can submit merge requests, or report issues.

## License

Licensed under the terms of the [GNU General Public License v3](LICENSE).
