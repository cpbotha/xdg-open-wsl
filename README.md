xdg-open-wsl is an xdg-open replacement for WSL that opens files and links using Windows apps.

For WSL apps using X, e.g. emacs, this enables the opening of files using the relevant Windows tool.

## Installation.

Until I publish to pypi, the easiest is the following:

```shell
# make sure you have the latest pip
pip3 install --user --upgrade pip
# install xdg-open-wsl using your latest pip
pip install --user git+https://github.com/cpbotha/xdg-open-wsl.git
# ensure that the newly installed xdg-open is active
# the following command should show something like /home/username/.local/bin/xdg-open
which xdg-open
```
