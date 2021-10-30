#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
from os import path
from sys import platform

class bColors:
    WARNING = "\033[93m"
    ERROR   = "\033[91m"
    MESSAGE = "\033[90m"
    RESET   = "\033[0m"

class OutType:
    FINAL = 'FINAL'

class Toolchain:
    def __init__(self, ext, toolchain):
        self.extension = ext
        self.toolchain = toolchain

TOOLCHAINS = {
    'cpp': Toolchain('cpp', 'g++'),
    'c': Toolchain('c', 'gcc')
}

CONFIG_NAME = "buildmec.json"
BIN_PATH    = "bin/"
SRC_PATH    = "src/"
VERSION     = "1.1"

PREFIX = '-' if platform != 'win32' else '/'
prefixed = lambda short, full: [PREFIX + short, (PREFIX*2) + full]

pcolor = lambda msg, col: print(f"{col}{msg}{bColors.RESET}")
perror = lambda msg: pcolor(msg, bColors.ERROR)
pwarn  = lambda msg: pcolor(msg, bColors.WARNING)
pmsg   = lambda msg: pcolor(msg, bColors.MESSAGE)

def write_default_config(toolchain):
    tc = TOOLCHAINS.get(toolchain)
    default_out  = { OutType.FINAL: 'main' }
    default_data = { "bin-path": BIN_PATH, "src-path": SRC_PATH, "build-order": [f"main.{tc.extension}"], "out": default_out }
    
    if toolchain == 'c':
        default_data['comp'] = { "toolchain": tc.toolchain }

    with open(CONFIG_NAME, 'w+') as f:
        json.dump(default_data, f, indent=4)

def write_starter_code(toolchain):
    include = "#include <iostream>" if toolchain == 'cpp' else "#include <stdio.h>"
    mainsig = "int main()" if toolchain == 'cpp' else "int main(int argc, char *argv[])"
    stdout  = 'std::cout << "Hello, world!" << std::endl;' if toolchain == 'cpp' else 'printf("Hello, world!\\n");'
    tc = TOOLCHAINS.get(toolchain)

    with open(SRC_PATH + f"main.{tc.extension}", 'w+') as f:
        f.write(f"{include}\n\n")
        f.write(f"{mainsig} {{\n")
        f.write(f"    {stdout}\n")
        f.write( "    return 0;\n")
        f.write( "}")

def reset_json(toolchain):
    ans = input("Restore buildmec.json to defaults? (Type 'YES' to continue) ")
    if (ans.lower() == 'yes'):
        write_default_config(toolchain)

def get_build_config():
    if not path.exists(CONFIG_NAME):
        perror("BuildMeC is not initialized.")
        return {}
    else:
        with open(CONFIG_NAME) as f:
            data = json.load(f)
            return data

def init_dirs(config):
    dirs = [ config['src-path'], config['bin-path'] ]
    for dir in dirs:
        if not path.exists(dir): os.makedirs(dir)

def initialize(toolchain):
    if path.exists(CONFIG_NAME):
        reset_json(toolchain)
    else:
        write_default_config(toolchain)

    init_dirs(get_build_config())

    if not path.exists(SRC_PATH + "main.cpp"): write_starter_code(toolchain)
    quit()

def get_out_path(config, ot):
    bin_path = config['bin-path']
    out = config['out'][ot]
    return bin_path + out

def get_tool_chain(config):
    if 'comp' in config:
        comp = config['comp']
        tool = comp.get('toolchain', 'CPP')
        flags = comp.get('flags', '')
        valid_toolchains = map(lambda t: t.toolchain, TOOLCHAINS.values())
        return tool if tool in valid_toolchains else 'g++', flags.split(' ')
    return 'g++', []


def execute_in_shell(cmd, show=True):
    if show: pmsg(" ".join(cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    _, error = process.communicate()
    if error: print(error)

def compile(config):
    # Build order is reversed in json config to make adding cpp files easier
    build_order = config['build-order']
    build_order.reverse()
    src_path = config['src-path']
    bin_out = get_out_path(config, OutType.FINAL)

    init_dirs(config)
    toolchain, flags = get_tool_chain(config)

    bash_cmd = [toolchain, *flags]
    if '' in flags: bash_cmd.remove('')
    for source_file in build_order:
        source_with_path = src_path + source_file
        if path.exists(source_with_path):
            bash_cmd.append(source_with_path)
        else:
            pwarn(f"'{source_with_path}' does not exists. Not adding to compilation.")
    bash_cmd.extend(['-o', bin_out])

    if len(bash_cmd) <= 3: quit() # Quit if no cpp files added to path

    execute_in_shell(bash_cmd)
    if path.exists(bin_out):
        execute_in_shell(['chmod', '+x', bin_out], show=False)

def run_project(config):
    os.system('./' + get_out_path(config, OutType.FINAL))

################################
#=======>-----MAIN-----<=======#
################################
def main():
    parser = argparse.ArgumentParser(description="Simple cpp project builder.", prefix_chars=PREFIX)
    parser.add_argument(*prefixed('v', 'version'), action='version', version="BuildMeC " + VERSION)
    parser.add_argument(*prefixed('i', 'init'), nargs='?', const='cpp', choices=TOOLCHAINS.keys(), help="Creates the buildmec.json config file.")
    parser.add_argument(*prefixed('c', 'compile'), action='store_true', help="Creates an object file inside the specified bin directory.")
    parser.add_argument(*prefixed('r', 'run'), action="store_true", default=False, help="Runs binary.")

    args = parser.parse_args()
    
    if args.init:
        initialize(args.init.lower())

    config = get_build_config()

    if args.compile and config:
        compile(config)

    # == RUN AFTER ALL OPERATIONS == #
    if args.run:
        run_project(config)

if __name__ == "__main__":
    main()