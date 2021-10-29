#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
from os import path
from sys import platform
from typing import Final

class bColors:
    WARNING = "\033[93m"
    ERROR   = "\033[91m"

    RESET   = "\033[0m"

class OutType:
    FINAL = 'FINAL'

CONFIG_NAME = "buildmec.json"
BIN_PATH    = "bin/"
SRC_PATH    = "src/"
VERSION     = "1.0"

PREFIX = '-' if platform != 'win32' else '/'
prefixed = lambda short, full: [PREFIX + short, (PREFIX*2) + full]

def write_default_config():
    default_data = { "bin-path": BIN_PATH, "src-path": SRC_PATH, "build-order": ["main.cpp"] }
    with open(CONFIG_NAME, 'w+') as f:
        json.dump(default_data, f, indent=4)

def write_starter_code():
    with open(SRC_PATH + "main.cpp", 'a+') as f:
        f.write("#include <iostream>\n\n")
        f.write("int main() {\n")
        f.write('    std::cout << "Hello world!" << std::endl;\n')
        f.write("    return 0;\n")
        f.write("}")

def reset_json():
    ans = input("Restore buildmec.json to defaults? (Type 'YES' to continue) ")
    if (ans.lower() == 'yes'):
        write_default_config()

def get_build_config():
    if not path.exists(CONFIG_NAME):
        print(f"{bColors.ERROR}BuildMeC is not initialized.{bColors.RESET}")
        return {}
    else:
        with open(CONFIG_NAME) as f:
            data = json.load(f)
            return data

def init_dirs(config):
    dirs = [ config['src-path'], config['bin-path'] ]
    for dir in dirs:
        if not path.exists(dir): os.makedirs(dir)

def initialize():
    if path.exists(CONFIG_NAME):
        reset_json()
    else:
        write_default_config()

    init_dirs(get_build_config())
    # if not path.exists('src'): os.makedirs('src')
    # if not path.exists('bin'): os.makedirs('bin')
    if not path.exists(SRC_PATH + "main.cpp"): write_starter_code()
    quit()

def get_out_path(config, ot):
    bin_path = config['bin-path']
    out = config['out'][ot]
    return bin_path + out

def execute_in_shell(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error: print(error)

def compile(config):
    # Build order is reversed in json config to make adding cpp files easier
    build_order = config['build-order']
    build_order.reverse()
    src_path = config['src-path']
    bin_out = get_out_path(config, OutType.FINAL)

    init_dirs(config)

    bash_cmd = ['g++']
    for source_file in build_order:
        source_with_path = src_path + source_file
        if path.exists(source_with_path):
            bash_cmd.append(source_with_path)
        else:
            print(f"{bColors.WARNING}'{source_with_path}' does not exists. Not adding to compilation.{bColors.RESET}")
    bash_cmd.extend(['-o', bin_out])

    if len(bash_cmd) <= 3: quit() # Quit if no cpp files added to path

    execute_in_shell(bash_cmd)
    if path.exists(bin_out):
        execute_in_shell(['chmod', '+x', bin_out])

def run_project(config):
    os.system('./' + get_out_path(config, OutType.FINAL))

################################
#=======>-----MAIN-----<=======#
################################
def main():
    parser = argparse.ArgumentParser(description="Simple cpp project builder.", prefix_chars=PREFIX)
    parser.add_argument(*prefixed('v', 'version'), action='version', version="BuildMeC " + VERSION)
    parser.add_argument(*prefixed('i', 'init'), action='store_true', default=False, help="Creates the buildmec.json config file.")
    parser.add_argument(*prefixed('c', 'compile'), action='store_true', help="Creates an object file inside the specified bin directory.")
    parser.add_argument(*prefixed('r', 'run'), action="store_true", default=False, help="Runs binary once project is finished building.")

    args = parser.parse_args()
    
    if args.init:
        initialize()

    config = get_build_config()

    if args.compile and config:
        compile(config)

    # == RUN AFTER ALL OPERATIONS == #
    if args.run:
        run_project(config)

if __name__ == "__main__":
    main()