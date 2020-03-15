#!/usr/bin/env python3

# xdg-open replacement for WSL, by Charl P. Botha <cpbotha@vxlabs.com>, that opens files and links using Windows apps.
# see the README.md for more information.

import logging
import os
import re
import sys
import subprocess

import click

MYDIR = os.path.dirname(os.path.abspath(sys.argv[0]))

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# taken from https://stackoverflow.com/a/29215357/532513
# currently using only escape_for_cmd_exe
def escape_argument(arg):
    # Escape the argument for the cmd.exe shell.
    # See http://blogs.msdn.com/b/twistylittlepassagesallalike/archive/2011/04/23/everyone-quotes-arguments-the-wrong-way.aspx
    #
    # First we escape the quote chars to produce a argument suitable for
    # CommandLineToArgvW. We don't need to do this for simple arguments.

    if not arg or re.search(r'(["\s])', arg):
        arg = '"' + arg.replace('"', r"\"") + '"'

    return escape_for_cmd_exe(arg)


def escape_for_cmd_exe(arg):
    """Escape an argument string to be suitable to be passed to cmd.exe on Windows

    taken from https://stackoverflow.com/a/29215357/532513

    This method takes an argument that is expected to already be properly
    escaped for the receiving program to be properly parsed. This argument
    will be further escaped to pass the interpolation performed by cmd.exe
    unchanged.

    Any meta-characters will be escaped, removing the ability to e.g. use
    redirects or variables.

    @param arg [String] a single command line argument to escape for cmd.exe
    @return [String] an escaped string suitable to be passed as a program
      argument to cmd.exe
    """

    meta_chars = '()%!^"<>&|'
    meta_re = re.compile("(" + "|".join(re.escape(char) for char in list(meta_chars)) + ")")
    meta_map = {char: "^%s" % char for char in meta_chars}

    def escape_meta_chars(m):
        char = m.group(1)
        return meta_map[char]

    return meta_re.sub(escape_meta_chars, arg)


@click.command()
@click.option("--logfile")
@click.argument("file_or_url")
def main(logfile, file_or_url):
    """Drop-in replacement for xdg-open on WSL systems that will open filename or URL using Windows.

    Use this to have your WSL X-application open files and links in the corresponding Windows application.
    I use it for Emacs running on WSL to open links and attachments in mu4e emails, and files and links from
    orgmode and dired.

    If the argument is a url starting with http(s) or zotero (special case for linking to zotero collections),
    it is opened with the default Windows handler, typically your browser.

    If the argument is a filename, its true location is determined. If the file is on the NTFS filesystem,
    it is passed as a standard full "D:\\my\\path\\file.ext" to Windows for handling. If it is on the WSL
    filesystem, it is transformed to a "wsl$\\"-style URI and passed to Windows for handling.
    """

    fn = file_or_url

    if logfile is not None:
        file_handler = logging.FileHandler(logfile)
        logger.addHandler(file_handler)

    # if we get passed a normal url by e.g. browse-url.el, just open it directly
    if re.match(r"^(https?|zotero):.*", fn):
        # to open web-links, we currently use "cmd.exe /c start http://your.url"
        # after a few months of testing, this has proven reliable for normal links than explorer
        # for cmd.exe special characters such as & and (, often occurring in URLs, have to be escaped.
        sp_run_arg = ["cmd.exe", "/c", "start", escape_for_cmd_exe(fn)]
        # sp_run_arg = ["explorer.exe", escape_for_cmd_exe(fn)]
        logger.info(f"http(s) -> subprocess.run() -> {sp_run_arg}")
        subprocess.run(sp_run_arg)
        return

    # sometimes we get passed a file:// prefix that has to be stripped before
    # realpath gets to it
    file_prefix = "file://"
    if fn.startswith(file_prefix):
        fn = fn[len(file_prefix) :]

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
        # i.e. convert /linux/filename.pdf to "\\\\wsl$\\Ubuntu-18.04\\linux\\filename.pdf"
        wdn = os.environ.get("WSL_DISTRO_NAME", "Ubuntu-18.04")
        winfn = f"\\\\wsl$\\{wdn}{bsfn}"

    sp_run_arg = ["explorer.exe", winfn]
    logger.info("====================>")
    logger.info(f"http(s) -> subprocess.run() -> {sp_run_arg}")
    completed_process = subprocess.run(sp_run_arg)
    logger.info(completed_process)
    logger.info("================DONE.")
    # subprocess.run(["cmd.exe", "/c", "start", "", winfn])


if __name__ == "__main__":
    main()
