import argparse as ap
import os
import re
import sys
from typing import List, Dict, Set, Optional

import piraha

def die(s:str):
    print(s)
    print("Failed")
    exit(1)

class ThornInfo:
    def __init__(self, name: str, arr: str, dir: str, requires: List[str], provides: List[str], src_files: List[str])->None:
        self.name = name
        self.arr = arr
        self.dir = dir
        self.requires = requires
        self.provides = provides
        self.src_files = src_files

    def __str__(self):
        return f"{self.name} ( arr='{self.arr}', requires={self.requires}, provides={self.provides} )"

    def __repr__(self):
        return self.__str__()


def find_src_files(thorn_dir:str)->List[str]:
    src_files: List[str] = list()

    # TODO: The parsing of make.code.defn leaves much to be desired at the moment
    with open(f"{thorn_dir}/src/make.code.defn", "r") as fd:
        for line in fd.readlines():
            if line.startswith("#"):
                continue
            for s in re.findall(r'[\w/-]+\.\w+', line):
                if os.path.exists(f"{thorn_dir}/src/{s}"):
                    src_files.append(s)

    return src_files


class Cactus:
    def __init__(self, cactus_dir:str=f"{os.environ.get('HOME','')}/Cactus", config:str="sim"):
        self.cactus_dir = cactus_dir
        self.config = config
        self.config_dir = f"{self.cactus_dir}/configs/{config}"
        self.thorns : Dict[str,ThornInfo] = dict()
        self.providers : Dict[str,ThornInfo] = dict()
        self.capabilities : Dict[str,ThornInfo] = dict()
        self.link_options: Set[str] = set()
        self.link_libraries: Set[str] = set()
        self.link_options.add("-L.")

        if not os.path.exists(self.config_dir):
            raise Exception(f"Cactus config '{config}' does not exist.")
        self.config_grammar, self.config_rule = piraha.parse_peg_file(f"{self.cactus_dir}/src/piraha/pegs/config.peg")
        self.interface_grammar, self.interface_rule = piraha.parse_peg_file(f"{self.cactus_dir}/src/piraha/pegs/interface.peg")
        self._identify_thorns()

        reqs, provides = self._requires_and_provides(f"{self.cactus_dir}/src")
        src_files = find_src_files(self.cactus_dir)
        self.thorns["Cactus"] = ThornInfo("Cactus", "flesh", f"{self.cactus_dir}/src", reqs, provides, src_files)

        self._find_link_options()
        self.link_libraries.add("gfortran")

    def _find_link_options(self) -> None:
        for thorn_info in self.thorns.values():
            for capability in thorn_info.provides:
                self.capabilities[capability] = thorn_info
        for capability, thorn_info in self.capabilities.items():
            # TODO: Hack
            capability_name : str
            if capability == "OPENPMD_API":
                capability_name = "OPENPMD"
            else:
                capability_name = capability
            file = f"{self.cactus_dir}/configs/{self.config}/bindings/Configuration/Capabilities/make.{capability}.defn"
            assert os.path.exists(file), f"{file} does not exist"
            with open(file, "r") as fd:
                for line in fd.readlines():
                    if g := re.match(fr"{capability_name}_LIBS\s*=\s*(.*\S)", line):
                        for lib in re.split(r'\s+', g.group(1)):
                            self.link_libraries.add(lib)
                    elif g := re.match(fr"{capability_name}_LIB_DIRS\s*=\s*(.*\S)", line):
                        for lib_dir in re.split(r'\s+', g.group(1)):
                            self.link_options.add("-L" + lib_dir)

    def _identify_thorns(self) -> None:
        thorn_list_file = f"{self.cactus_dir}/configs/{self.config}/ThornList"
        assert os.path.exists(thorn_list_file), f"No such file: '{thorn_list_file}'"
        with open(thorn_list_file, "r") as fth:
            for line in fth.readlines():
                if g := re.match(r'^(\w+)/(\w+)', line):
                    arr = g.group(1)
                    thorn_name = g.group(2)
                    thorn_dir = f"{self.cactus_dir}/arrangements/{arr}/{thorn_name}"
                    assert os.path.exists(f"{thorn_dir}/param.ccl")
                    r, p = self._requires_and_provides(thorn_dir)
                    sf = find_src_files(thorn_dir)
                    self.thorns[thorn_name] = ThornInfo(thorn_name, arr, thorn_dir, r, p, sf)
                    for capability in p:
                        self.providers[capability] = self.thorns[thorn_name]

    def provides_functions(self, thorn_name: str) -> bool:
        thorn_dir = self.thorns[thorn_name].dir
        interface_file = f"{thorn_dir}/interface.ccl"
        matcher = piraha.parse_src(self.interface_grammar, self.interface_rule, interface_file)
        r = matcher.matches()
        assert r
        for group in matcher.gr.children:
            if group.getPatternName() == "FUNC_GROUP":
                if group.has(0, "FUNCTION"):
                    if group.group(0).has(0, "PROVIDES_FUN"):
                        return True
        return False

    def _requires_and_provides(self, thorn_dir: str):
        requires = []
        provides = []
        config_file = f"{thorn_dir}/configuration.ccl"
        if not os.path.exists(config_file):
            return requires, provides
        matcher = piraha.parse_src(self.config_grammar, self.config_rule, config_file)
        r = matcher.matches()
        assert r
        gr = matcher.gr
        for child in gr.children:
            if child.getPatternName() == "provopt":
                key = child.group(0).substring().upper()
                val = child.group(1).substring().upper()
                if key in ["OPTIONAL", "REQUIRES"]:
                    requires.append(val)
                elif key == "PROVIDES":
                    provides.append(val)
                else:
                    assert f"Not handled: {key}"
            elif child.getPatternName() == "requires":
                for req in child.children:
                    if req.getPatternName() == "name_with_ver":
                        requires.append(req.group(0, "name").substring().upper())
                    elif req.getPatternName() == "thorns":
                        for th in req.children:
                            requires.append(th.substring().upper())
                    else:
                        assert False, child.dump()
            else:
                assert f"Not handled: {child.dump()}"
        return requires, provides

    def find_includes(self, thorn_name: str) -> Set[str]:
        assert thorn_name in self.thorns, f"Cannot find thorn: {thorn_name}"
        thorn_info = self.thorns[thorn_name]
        check_reqs = thorn_info.requires
        old_reqs = set()
        done = False
        while not done:
            new_reqs = set()
            for capability in check_reqs:
                th = self.providers.get(capability, None)
                if th is None:
                    continue
                req_thorn_info = self.thorns[th.name]
                for cap in req_thorn_info.requires:
                    new_reqs.add(cap)
                old_reqs.add(capability)
            check_reqs = set()
            done = True
            for new_req in new_reqs:
                if new_req not in old_reqs:
                    check_reqs.add(new_req)
                    done = False
        incs : Set[str] = set()
        for capability in old_reqs:
            for inc in self._find_includes(capability):
                incs.add(inc)
        return incs

    def _find_includes(self, capability:str)->Set[str]:
        inc_dirs : Set[str] = set()
        file = f"{self.cactus_dir}/configs/{self.config}/bindings/Configuration/Capabilities/make.{capability}.defn"
        if not os.path.exists(file):
            print("capabilities file does not exist:", file)
            return set()
        with open(file, "r") as fd:
            for line in fd.readlines():
                g = re.search(fr'{capability}_INC_DIRS\s*=\s*(.*\S)', line)
                if g:
                    for path in re.split(r'\s+', g.group(1)):
                        inc_dirs.add(path)
        return inc_dirs

    def nice_path(self, path:str)->str:
        if path.startswith(self.config_dir):
            return "${CONFIG}" + path[len(self.config_dir):]
        elif path.startswith(self.cactus_dir):
            return "${CCTK_HOME}" + path[len(self.cactus_dir):]
        else:
            return path


if __name__ == "__main__":
    cactus = Cactus()
    for thorn in cactus.thorns.values():
        #print(thorn)
        #print(thorn.src_files)
        print(cactus.find_includes(thorn.name))
        pass
    # print(cactus.providers)
    # print(cactus.capabilities)
    # print(cactus.link_libraries)
    # print(cactus.link_options)


def make_argument_parser(name:str):
    argp = ap.ArgumentParser(prog="CactusCmake", description="Cmake file generator for Cactus")
    argp.add_argument("--config", type=str, default=None, help="Cactus config name, e.g. 'sim'")
    argp.add_argument("--cactus-root",type=str, default=f"{os.environ['HOME']}/Cactus", help="Cactus root directory")
    parsed_args = argp.parse_args(sys.argv[1:])
    cactus_dir:str = parsed_args.cactus_root
    config:Optional[str] = parsed_args.config
    print(f"Using Cactus root dir: '{cactus_dir}'...")
    if config is not None:
        print(f"Using config '{config}'...")

    if not os.path.exists(f"{cactus_dir}"):
        die("Cactus root directory, '{cactus_dir}', does not exist")

    if config is None:
        if os.path.exists(f"{cactus_dir}/configs"):
            configs_dir = f"{cactus_dir}/configs"
            configs_list = os.listdir(configs_dir)
            if len(configs_list) == 1:
                config = configs_list[0]
            else:
                print("Configs that exist:")
                for cfg in configs_list:
                    print(" ",cfg)
                die("Please choose a config")
    return argp, cactus_dir, config
