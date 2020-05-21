# xdg-open-wsl

xdg-open-wsl is an xdg-open replacement for WSL that opens files and links using Windows apps.

For WSL apps using X, e.g. emacs, this enables the opening of files using the relevant Windows tool.

![Run Tests](https://github.com/cpbotha/xdg-open-wsl/workflows/Run%20Tests/badge.svg)

## Installation.

Until I publish to pypi, the easiest is option 1.

### Option 1: Install from github using pip.

```shell
# make sure you have the latest pip
# NOTE: you HAVE to do this upgrade, else pip install won't know what to do without setup.py!
pip3 install --user --upgrade pip
# install xdg-open-wsl using your latest pip
pip install --user git+https://github.com/cpbotha/xdg-open-wsl.git
# ensure that the newly installed xdg-open is active
# the following command should show something like /home/username/.local/bin/xdg-open
which xdg-open
```

### Option 2: Use the main script directly.

Download only the [xdg_open_wsl.py
script](https://github.com/cpbotha/xdg-open-wsl/blob/master/xdg_open_wsl/xdg_open_wsl.py)
and save it as `xdg-open` into your `~/.local/bin/` or `~/bin/`, whichever is
in your `PATH` before any system `xdg-open`.

Ensure with `which xdg-open` that your new `xdg-open` is preferred.

## FAQ.

### Does this work for Emacs on WSL?

Why yes, of course it does. This is also why I wrote this in the first place.

Importantly, there is a "bug" somewhere between Emacs and the WSL which will cause `org-open-file` to block forever.

Follow the advice in my blog post [Patch Emacs org-open-file using advice](https://vxlabs.com/2020/03/07/patch-emacs-org-open-file-using-advice/) to fix this behaviour.

In short, simply add this to your `init.el`:

```emacs-lisp
;; fix org-open-file for wsl by temporarily replacing start-process-shell-command with call-process-shell-command
;; if we don't do this, emacs on WSL will block forever trying to open exported file with windows handler
(defun wsl-fix-org-open-file (orig-org-open-file &rest args)
  ;; temporarily replace function,
  ;; see https://endlessparentheses.com/understanding-letf-and-how-it-replaces-flet.html
  (cl-letf (((symbol-function 'start-process-shell-command) #'call-process-shell-command))
    (apply orig-org-open-file args)))

(advice-add #'org-open-file :around #'wsl-fix-org-open-file)
```
