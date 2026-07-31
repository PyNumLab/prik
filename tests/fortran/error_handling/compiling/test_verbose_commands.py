import shlex
import sys

from x2py.compiling.compilers import Compiler


def test_run_command_verbose_prints_replayable_command(capsys):
    cmd = [sys.executable, "-c", ""]

    returned = Compiler.run_command(cmd, verbose=1)

    assert returned == tuple(cmd)
    output = capsys.readouterr().out.splitlines()
    assert output == [shlex.join(cmd)]
