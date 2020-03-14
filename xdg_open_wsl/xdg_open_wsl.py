#!/usr/bin/env python3

# script by cpbotha which replaces xdg-open on WSL
# for apps using X, e.g. emacs, this enables the opening of files using the relevant Windows tool

# make sure that (browse-url-can-use-xdg-open) evaluates to true by adding
# (getenv "WSLENV") to the list of OR conds

# for org-open-file, you might have to change start-proces-shell-command in org.el
# to call-process-shell-command, else you'll see this:

    # - if this is called via emacs -> sensible-browser -> xdg-open the
    #   invoked /init explorer.exe / cmd.exe blocks forever, shows nothing,
    #   and ends up eating 100% CPU
    # - invoking sensible-browser directly from shell works
    # - invoking xdg-open directly from emacs works
    # - symlinking sensible-browser to xdg-open does NOT work.


import logging
import os
import re
import sys
import subprocess

MYDIR = os.path.dirname(os.path.abspath(sys.argv[0]))

logger = logging.getLogger()
file_handler = logging.FileHandler(os.path.join(MYDIR, 'xdg-open.log'))
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)

# taken from https://stackoverflow.com/a/29215357/532513
def escape_argument(arg):
    # Escape the argument for the cmd.exe shell.
    # See http://blogs.msdn.com/b/twistylittlepassagesallalike/archive/2011/04/23/everyone-quotes-arguments-the-wrong-way.aspx
    #
    # First we escape the quote chars to produce a argument suitable forp
    # CommandLineToArgvW. We don't need to do this for simple arguments.

    if not arg or re.search(r'(["\s])', arg):
        arg = '"' + arg.replace('"', r'\"') + '"'

    return escape_for_cmd_exe(arg)

# taken from https://stackoverflow.com/a/29215357/532513
def escape_for_cmd_exe(arg):
    # Escape an argument string to be suitable to be passed to
    # cmd.exe on Windows
    #
    # This method takes an argument that is expected to already be properly
    # escaped for the receiving program to be properly parsed. This argument
    # will be further escaped to pass the interpolation performed by cmd.exe
    # unchanged.
    #
    # Any meta-characters will be escaped, removing the ability to e.g. use
    # redirects or variables.
    #
    # @param arg [String] a single command line argument to escape for cmd.exe
    # @return [String] an escaped string suitable to be passed as a program
    #   argument to cmd.exe

    meta_chars = '()%!^"<>&|'
    meta_re = re.compile('(' + '|'.join(re.escape(char) for char in list(meta_chars)) + ')')
    meta_map = { char: "^%s" % char for char in meta_chars }

    def escape_meta_chars(m):
        char = m.group(1)
        return meta_map[char]

    return meta_re.sub(escape_meta_chars, arg)

# convert /linux/filename.pdf to "\\\\wsl$\\Ubuntu-18.04\\linux\\filename.pdf"
def main():
    fn = sys.argv[1]

    # if we get passed a normal url by e.g. browse-url.el, just open it directly
    if re.match(r'^(https?|zotero):.*', fn):
        # for opening weblinks from Emacs with xdg-open,
        # "cmd.exe /c start fn" works but "explorer fn" does not
        # also, for cmd.exe special characters such as & and (, often occurring in URLs, have to be escaped.
        # mysteriously on 2019-08-24, cmd.exe stops working, explorer.exe starts working...
        # with evernote inbox link, cmd.exe works, explorer.exe does not. ARGH.
        sp_run_arg = ["cmd.exe", "/c", "start", escape_for_cmd_exe(fn)]
        #sp_run_arg = ["explorer.exe", escape_for_cmd_exe(fn)]
        logger.info(f"http(s) -> subprocess.run() -> {sp_run_arg}")
        subprocess.run(sp_run_arg)
        return

    # sometimes we get passed a file:// prefix that has to be stripped before
    # realpath gets to it
    file_prefix = 'file://'
    if fn.startswith(file_prefix):
        fn = fn[len(file_prefix):]

    # make sure we have full, real location (absolute and symlinks resolved)
    real_fn = os.path.realpath(fn)

    # replace every / with a double \\ (escaped backslash)
    bsfn = real_fn.replace("/", "\\")
    
    if bsfn.startswith("\\c\\"):
        # oooer, this file lives on the native Windows side, so complete the address
        winfn = bsfn.replace("\\c\\", "c:\\")
    else:
        # this file lives somewhere in WSL, so:
        # prepend with win-compatible way to see that file
        winfn = f"\\\\wsl$\\Ubuntu-18.04{bsfn}"

    sp_run_arg = ["explorer.exe", winfn]
    logger.info("====================>")
    logger.info(f"http(s) -> subprocess.run() -> {sp_run_arg}")
    completed_process = subprocess.run(sp_run_arg)
    logger.info(completed_process)
    logger.info("================DONE.")
    #subprocess.run(["cmd.exe", "/c", "start", "", winfn])


if __name__ == "__main__":
    main()
