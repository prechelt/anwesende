import os
import re
import sys

PATCHVAR_PREFIX = "PATCH_"


def patch_file(filename: str) -> None:
    with open(filename, 'rt', encoding='UTF-8') as input:
        for line in input:
            sys.stdout.write(patched(line))


def patched(line: str) -> str:
    var_match = re.match(r"^(\w+)\s*=", line)
    if var_match:
        varname = var_match.group(1)
        patchvarname = PATCHVAR_PREFIX + varname
        patchvalue = os.environ.get(patchvarname, None)
        if patchvalue is None:
            return line  # unpatched assignment line
        else:
            return "%s=%s\n" % (varname, patchvalue)  # patched assignment line
    else:
        return line  # non-assignment line


if __name__ == '__main__':
    for arg in sys.argv:
        if arg.endswith('.py'):
            continue  # skip yourself when called with python
        patch_file(arg)
