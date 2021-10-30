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
    default_out  = { 'FINAL': 'main', 'obj-path': '' }
    default_data = { "bin-path": BIN_PATH, "src-path": SRC_PATH, "sources": [f"main.{tc.extension}"], "out": default_out }
    
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

def get_out_path(config, ot):
    bin_path = config['bin-path']
    out = config['out'][ot]
    return bin_path + out

def init_dirs(config):
    dirs = [ config['src-path'], config['bin-path'], get_out_path(config, 'obj-path') ]
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
    if error: perror(error)

def just_filename(file_path):
    file = file_path.split('/')[-1]
    return file.rsplit('.', 1)[0]

def compile_o(sources, bash_cmd, src_path, obj_path):
    objs = []
    for source_file in sources:
        source_with_path = src_path + source_file
        cmd = bash_cmd.copy()
        if path.exists(source_with_path):
            o_path = f"{obj_path}{just_filename(source_with_path)}.o"
            objs.append(o_path)
            cmd.extend([ source_with_path, '-c', '-o', o_path ])
            execute_in_shell(cmd)
        else:
            pwarn(f"'{source_with_path}' does not exist. Not adding to compilation.")
    return objs

def compile(config):
    # Build order is reversed in json config to make adding cpp files easier
    build_order = config['sources']
    src_path = config['src-path']
    obj_path = get_out_path(config, 'obj-path')
    bin_out = get_out_path(config, 'FINAL')

    init_dirs(config)
    toolchain, flags = get_tool_chain(config)

    bash_cmd = [toolchain, *flags]
    if '' in flags: bash_cmd.remove('')
    
    compiled = compile_o(build_order, bash_cmd, src_path, obj_path)
    if not compiled:
        perror("Not sources to compile.")
        quit()
    
    bash_cmd.extend([*compiled, '-o', bin_out])

    execute_in_shell(bash_cmd)
    if path.exists(bin_out):
        execute_in_shell(['chmod', '+x', bin_out], show=False)

def run_project(config, args):
    cmd = f"./{get_out_path(config, 'FINAL')} {' '.join(args)}" # ./{out} [args...]
    os.system(cmd)

################################
#=======>-----MAIN-----<=======#
################################
def main():
    parser = argparse.ArgumentParser(description="Simple cpp project builder.", prefix_chars=PREFIX)
    parser.add_argument(*prefixed('v', 'version'), action='version', version="BuildMeC " + VERSION)
    parser.add_argument(*prefixed('i', 'init'), nargs='?', const='cpp', choices=TOOLCHAINS.keys(), help="Creates the buildmec.json config file.")
    parser.add_argument(*prefixed('c', 'compile'), action='store_true', help="Creates an object file inside the specified bin directory.")
    parser.add_argument(*prefixed('r', 'run'), nargs='*', default=False, help="Runs binary.")

    args = parser.parse_args()

    if args.init:
        initialize(args.init.lower())

    config = get_build_config()

    if args.compile and config:
        compile(config)

    # == RUN AFTER ALL OPERATIONS == #
    if args.run != False:
        run_project(config, args.run)

if __name__ == "__main__":
    main()