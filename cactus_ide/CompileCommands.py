import os

from cactus_ide.cactus import Cactus, ThornInfo, make_argument_parser
import json
import re

def main():
    argp, cactus_dir, config = make_argument_parser("CompileCommands")
    cactus = Cactus(cactus_dir=cactus_dir, config=config)

    jdata = list()
    for thorn_info in cactus.thorns.values():
        if thorn_info.name == "Cactus":
            pass #print(thorn_info)
        for src_file in thorn_info.src_files:
            inc_files = list()
            full_src_file = f"{thorn_info.dir}/src/{src_file}"
            assert os.path.exists(full_src_file)
            full_output = f"{cactus.config_dir}/build/{thorn_info.name}/{src_file}.o"
            for inc_file in cactus.find_includes(thorn_info.name):
                inc_files += [f"-I{inc_file}"]
            inc_files += [f"-I{cactus.cactus_dir}/arrangements/{thorn_info.arr}/{thorn_info.name}/src"]
            inc_files += [f"-I{cactus.cactus_dir}/arrangements/{thorn_info.arr}/{thorn_info.name}/src/include"]
            inc_files += [f"-I{cactus.cactus_dir}/src/include"]
            inc_files += [f"-I{cactus.cactus_dir}/arrangements"]
            inc_files += [f"-I{cactus.cactus_dir}/configs/{config}/bindings/Configuration/Thorns"]
            inc_files += [f"-I{cactus.cactus_dir}/configs/{config}/config-data"]
            inc_files += [f"-I{cactus.cactus_dir}/configs/{config}/bindings/include"]
            inc_files += [f"-I{cactus.cactus_dir}/configs/{config}/bindings/include/{thorn_info.name}"]

            ### Process dep files if present
            dep_dirs = set()
            if g := re.search(r'/(\w+)/src/(\w+)\.(c\w*)$', full_src_file):
                dep = f"{cactus_dir}/configs/{config}/build/{g.group(1)}/{g.group(2)}.{g.group(3)}.d"
                with open(dep, "r") as fd:
                    dep_contents = fd.read()
                for p in re.finditer(r'(/\S+)/[^/\s]+', dep_contents):
                    dep_dir = p.group(1)
                    if dep_dir.startswith("/usr") and dep_dir not in dep_dirs:
                        dep_dirs.add(dep_dir)
                        inc_files += [f"-I{dep_dir}"]

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
        print("compile_commands.json is generated")

if __name__ == "__main__":
    main()
