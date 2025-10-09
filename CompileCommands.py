import os

from cactus import Cactus, ThornInfo, make_argument_parser
import json

argp, cactus_dir, config = make_argument_parser("CompileCommands")
cactus = Cactus(cactus_dir=cactus_dir, config=config)

jdata = list()
for thorn_info in cactus.thorns.values():
    if thorn_info.name == "Cactus":
        print(thorn_info)
    for src_file in thorn_info.src_files:
        inc_files = list()
        full_src_file = f"{thorn_info.dir}/src/{src_file}"
        assert os.path.exists(full_src_file)
        full_output = f"{cactus.config_dir}/build/{thorn_info.name}/{src_file}.o"
        for inc_file in cactus.find_includes(thorn_info.name):
            inc_files += [f"-I{inc_file}"]
        item = {
            "arguments": [
                             "g++",
                             "-fopenmp",
                             "-Wall",
                             "-g",
                             "-O2",
                             "-c",
                             "-DCCODE"
                         ] + inc_files,
            "directory": f"{cactus.config_dir}/scratch",
            "file": full_src_file,
            "output": full_output
        }
        jdata.append(item)
        if os.path.islink(thorn_info.dir):
            rl = os.readlink(thorn_info.dir)
            alt_dir = os.path.realpath(f"{thorn_info.dir}/../{rl}")
            alt_path = f"{alt_dir}/src/{src_file}"
            alt_output = f"{cactus.config_dir}/build/{thorn_info.name}/{src_file}_2.o"
            if os.path.exists(alt_path):
                item = {
                    "arguments": [
                                     "g++",
                                     "-fopenmp",
                                     "-Wall",
                                     "-g",
                                     "-O2",
                                     "-c",
                                     "-DCCODE"
                                 ] + inc_files,
                    "directory": f"{cactus.config_dir}/scratch",
                    "file": alt_path,
                    "output": alt_output
                }
                jdata.append(item)

with open("compile_commands.json", "w") as fd:
    json.dump(jdata, fd, indent=2)

print("Working Directory:", os.getcwd())
