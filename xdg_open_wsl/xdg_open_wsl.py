#!/usr/bin/env python3

# xdg-open replacement for WSL that opens files and links using Windows apps.
# copyright 2020 by Charl P. Botha <cpbotha@vxlabs.com>,
# see the README.md for more information.

# https://github.com/cpbotha/xdg-open-wsl/

import logging
import os
import re
import sys
import subprocess
from typing import List, Tuple

import click

MYDIR = os.path.dirname(os.path.abspath(sys.argv[0]))

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# DEPRECATED, to be removed soon.
def build_mnt_to_drive_table() -> List[Tuple[str, str]]:
    """Using the mount command, figure out how windows drive letters are mounted in WSL."""
    table = []
    completed = subprocess.run("mount", stdout=subprocess.PIPE)
    # result of command above will be e.g.
    # C:\ on /mnt/c type drvfs (rw,noatime,uid=1000,gid=1000,umask=22,metadata,case=off)
    # D:\ on /mnt/d type drvfs (rw,noatime,uid=1000,gid=1000,umask=22,metadata,case=off)
    # but mount points can be configured anywhere. Mine are C:\ -> /c/ for example
    for l in completed.stdout.decode("utf-8").split("\n"):
        if "type drvfs" in l:
            # I find the first and the third, so I do a range from 0 to <3 but skip one with step=2
            # e.g. "/mnt/c" -> "C:\"
            drive, mount_point = l.split()[0:3:2]
            # make it "/mnt/c/" -> "C:/"
            table.append((f"{mount_point}/", drive[0:-1] + "/"))

    return table


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


# DEPRECATED, to be removed soon. Replaced by much simpler wslpath version below
def convert_filename_to_windows(fn: str, drive_lut: List[Tuple[str, str]], distro_name: str) -> str:
    """Given a filename, convert to Windows-compatible double-backslashed `D:\\my\\path` path or to
    `$wsl\\\\distro\\path` WSL-locator.
    """

    # sometimes we get passed a file:// prefix that has to be stripped before
    # realpath gets to it
    file_prefix = "file://"
    if fn.startswith(file_prefix):
        fn = fn[len(file_prefix) :]

    # make sure we have full, real location (absolute and symlinks resolved)
    real_fn = os.path.realpath(fn)

    # only if path starts with e.g. /mnt/c/ replace that with c:/
    on_wsl_fs = True
    for mount_point, drive in drive_lut:
        if real_fn.startswith(mount_point):
            # only replace the first occurrence, just in case
            real_fn = real_fn.replace(mount_point, drive, 1)
            # now we know for sure this is a file on the windows side
            on_wsl_fs = False
            # can only be on one windows drive, so we can stop looking
            break

    # replace every / with a double \\ (escaped backslash) as we're going to call windows now
    winfn = real_fn.replace("/", "\\")

    # winfn is now one of two things:
    # 1. windows path e.g. c:\\some\\path\\filename.ext -- we can open this directly
    # 2. WSL file e.g. \\home\\myuser\\Downloads\\somefile.ext -- we have to transform to wsl$ URI

    if on_wsl_fs:
        # case 2, his file lives somewhere in WSL, so:
        # prepend with win-compatible way to see that file
        # i.e. convert /linux/filename.pdf to "\\\\wsl$\\Ubuntu-18.04\\linux\\filename.pdf"
        winfn = f"\\\\wsl$\\{distro_name}{winfn}"

    return winfn


def convert_filename_to_windows_new(fn: str) -> str:
    # sometimes we get passed a file:// prefix that has to be stripped before
    # realpath gets to it
    file_prefix = "file://"
    if fn.startswith(file_prefix):
        fn = fn[len(file_prefix):]

    winfn = subprocess.check_output(["wslpath", "-aw", fn]).decode('utf-8').strip()
    return winfn


def get_explorer_path() -> str:
    """Get full WSL-path to explorer.exe

    Under some environments, explorer.exe is not on the WSL PATH, so we invoke it by its full WSL path.
    """
    return subprocess.check_output(["wslpath", "-u", r"c:\windows\explorer.exe"]).decode('utf-8').strip()


def get_cmd_path() -> str:
    """Get full WSL-path to cmd.exe

    Under some environments, cmd.exe is not on the WSL PATH, so we invoke it by its full WSL path,
    derived from its canonical Windows location.
    """
    return subprocess.check_output(["wslpath", "-u", r"c:\windows\system32/cmd.exe"]).decode('utf-8').strip()


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

    if logfile is not None:
        file_handler = logging.FileHandler(logfile)
        logger.addHandler(file_handler)

    # if we get passed a normal url by e.g. browse-url.el, just open it directly
    if re.match(r"^(https?|zotero):.*", file_or_url):
        # to open web-links, we currently use "cmd.exe /c start http://your.url"
        # after a few months of testing, this has proven reliable for normal links than explorer
        # for cmd.exe special characters such as & and (, often occurring in URLs, have to be escaped.
        sp_run_arg = [get_cmd_path(), "/c", "start", escape_for_cmd_exe(file_or_url)]
        # sp_run_arg = ["explorer.exe", escape_for_cmd_exe(fn)]
        logger.info(f"http(s) -> subprocess.run() -> {sp_run_arg}")
        subprocess.run(sp_run_arg)
        return

    # winfn = convert_filename_to_windows(
    #     file_or_url, build_mnt_to_drive_table(), os.environ.get("WSL_DISTRO_NAME", "Ubuntu-18.04")
    # )

    winfn = convert_filename_to_windows_new(file_or_url)

    # again here we could use explorer or cmd. In this case, I've had the most joy with explorer.exe
    sp_run_arg = [get_explorer_path(), winfn]
    logger.info("====================>")
    logger.info(f"http(s) -> subprocess.run() -> {sp_run_arg}")
    completed_process = subprocess.run(sp_run_arg)
    logger.info(completed_process)
    logger.info("================DONE.")
    # subprocess.run(["cmd.exe", "/c", "start", "", winfn])


if __name__ == "__main__":
    main()
