from xdg_open_wsl.xdg_open_wsl import convert_filename_to_windows


def test_wsl_filename():
    fn = "/tmp/remote-wsl-loc.txt"
    win_fn = convert_filename_to_windows(fn, [], "Ubuntu-20.04")
    assert win_fn == "\\\\wsl$\\Ubuntu-20.04\\tmp\\remote-wsl-loc.txt"


def test_win_filename():
    fn = "/mnt/c/Users/cpb/Downloads/mydoc.pdf"
    win_fn = convert_filename_to_windows(fn, [("/mnt/c/", "C:/")], "blat")
    assert win_fn == "C:\\Users\\cpb\\Downloads\\mydoc.pdf"


def test_file_prefix():
    fn = "file:///tmp/blat.txt"
    win_fn = convert_filename_to_windows(fn, [], "Ubuntu-20.04")
    assert win_fn == "\\\\wsl$\\Ubuntu-20.04\\tmp\\blat.txt"
