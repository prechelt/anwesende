# Python script for rewriting a docker env file.
# usage: patch_env dockerenv_input.env dockerenv_output.env
# Copies each input line to the output, except when it is of the form
#   VAR_X=value
# and an environment variable PATCH_VAR_X exists: then its value is used.
# Performs no error handling.

import os
import re
import sys

PATCHVAR_PREFIX = "PATCH_"


def patch_file(infile: str, outfile: str) -> None:
    with open(infile, 'rt', encoding='utf-8') as input, \
         open(outfile, 'wb') as output:
        for line in input:
            output.write(patched(line).encode('utf-8'))


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
    first = 2 if sys.argv[1].endswith('.py') else 1  # call: python patch_env.py in out 
    patch_file(sys.argv[first], sys.argv[first + 1])
