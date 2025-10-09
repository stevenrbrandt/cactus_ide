import os
import re
from typing import List, Dict, Optional

from cactus import Cactus, make_argument_parser

providers: Dict[str, str] = dict()

f_line_directives_setting : Optional[bool] = None

def find_f_line_directives(config)->bool:
    global f_line_directives_setting
    if f_line_directives_setting is not None:
        return f_line_directives_setting
    fname = f"{config}/config-data/make.config.defn"
    ret = False
    with open(fname) as fd:
        for line in fd.readlines():
            if g := re.match("export\\s+F_LINE_DIRECTIVES\\s+=\\s+(yes|no)"):
                print(f"F_LINE_DIRECTIVES={g.group(1)}")
                ret = g.group(1) == "yes"
    f_line_directives_setting = ret
    return ret

file_counter = 0
file_transform_counter = 0

file_contents = """
project(thorn_<THORN>)

<C_FILE_PROCS>

# Add the library
add_library(
    thorn_<THORN>
    STATIC
    ${CONFIG}/bindings/build/<THORN>/cctk_ThornBindings.c
    #${CONFIG}/build/<THORN>/cctk_Bindings/cctk_ThornBindings.c
    #${BUILD}/CactusBindings/Parameters/<THORN>_Parameters.c
    ${CONFIG}/bindings/Parameters/<THORN>_Parameters.c
    #${BUILD}/CactusBindings/Schedule/Schedule<THORN>.c
    ${CONFIG}/bindings/Schedule/Schedule<THORN>.c
    ${BINDINGS}/Variables/<THORN>.c
<FILES>
)

target_compile_options(
    thorn_<THORN>
    PRIVATE
    -DCCODE
    -fopenmp
    -rdynamic
    ${MPI_C_COMPILE_OPTIONS}
)

target_include_directories(
    thorn_<THORN>
    PUBLIC
      ${ARRANGEMENTS}/<ARR>/<THORN>/src
      ${CONFIG}/config-data
      ${CONFIG}/bindings/include
      ${CCTK_HOME}/src/include
      ${ARRANGEMENTS}
      ${CONFIG}/bindings/Configuration/Thorns
      ${CONFIG}/bindings/include/<THORN>
      ${ARRANGEMENTS}/<ARR>/<THORN>/src
      ${ARRANGEMENTS}/<ARR>/<THORN>/src/include
      ${MPI_C_INCLUDE_DIRS}
      <INC_DIRS>
)"""

flesh_file_contents = """
project(thorn_Cactus)

<C_FILE_PROCS>

# Add the library
add_library(
    thorn_Cactus
    STATIC
    ${CONFIG}/build/Cactus/cctk_Bindings/cctk_ThornBindings.c
    ${CONFIG}/build/CactusBindings/Parameters/Cactus_Parameters.c
    ${CONFIG}/build/CactusBindings/Schedule/ScheduleCactus.c
    ${BINDINGS}/Variables/Cactus.c
    ${BINDINGS}/Functions/RegisterThornFunctions.c
    ${BINDINGS}/Schedule/BindingsSchedule.c
    ${BUILD}/CactusBindings/Functions/AliasedFunctions.c
    ${BINDINGS}/Schedule/BindingsParameterRecovery.c
    ${BUILD}/CactusBindings/Functions/IsFunctionAliased.c
    ${BINDINGS}/Implementations/ImplementationBindings.c
    ${BINDINGS}/Parameters/BindingsParameters.c
    #${CCTK_HOME}/src/datestamp.c
    ${BINDINGS}/Variables/BindingsVariables.c
<FILES>
)

target_compile_options(
    thorn_Cactus
    PRIVATE
    -DCCODE
    -fopenmp
    -g
    ${MPI_C_COMPILE_OPTIONS}
)

target_include_directories(
    thorn_Cactus
    PUBLIC
      <INCS_DIRS>
      ${CONFIG}/config-data
      ${CONFIG}/bindings/include
      ${CCTK_HOME}/src/include
      ${CONFIG}/bindings/Configuration/Thorns
      ${CONFIG}/bindings/include/Cactus
      ${CONFIG}/bindings/include
      ${CCTK_HOME}/src/schedule
      ${CCTK_HOME}/src/piraha
      #${MPI_C_INCLUDE_DIRS}
)"""

# if test no = 'yes'; then echo '#line 1 "'/home/sbrandt/Cactus/arrangements/CactusNumerical/SummationByParts/src/All_Coeffs_mod.F90'"'; fi;
# cat /home/sbrandt/Cactus/arrangements/CactusNumerical/SummationByParts/src/All_Coeffs_mod.F90; } |
# perl -p -e 's.//.CCTK_AUTOMATICALLY_GENERATED_CONCATENATION_PROTECTION.g' |
# cpp -traditional  -D_OPENMP -I"/home/sbrandt/Cactus/arrangements/CactusNumerical/SummationByParts/src"
#   -I"/home/sbrandt/Cactus/configs/sim/config-data" -I"/home/sbrandt/Cactus/configs/sim/bindings/include"
#   -I"/home/sbrandt/Cactus/src/include" -I"/home/sbrandt/Cactus/arrangements" -I"/home/sbrandt/Cactus/configs/sim/bindings/Configuration/Thorns"
#   -I"/home/sbrandt/Cactus/configs/sim/bindings/include/SummationByParts" -I"/home/sbrandt/Cactus/arrangements/CactusNumerical/SummationByParts/src"
#   -I"/home/sbrandt/Cactus/configs/sim/bindings/include/SummationByParts"  -DFCODE -DF90CODE |
#   perl -p -e 's.CCTK_AUTOMATICALLY_GENERATED_CONCATENATION_PROTECTION.//.g' |
#   perl -p -e 's/__FORTRANFILE__/\"All_Coeffs_mod.F90\"/g' |
#   perl -s /home/sbrandt/Cactus/lib/sbin/f_file_processor.pl -free_format -line_directives=no
#     -source_file_name=/home/sbrandt/Cactus/arrangements/CactusNumerical/SummationByParts/src/All_Coeffs_mod.F90 > All_Coeffs_mod.f90

special_custom_command = """
add_custom_command(
    OUTPUT ${BUILD}/mkfort.sh
    COMMAND echo "perl -p -e 's.//.CCTK_AUTOMATICALLY_GENERATED_CONCATENATION_PROTECTION.g'" > 
    DEPENDS ${ARRANGEMENTS}/<ARR>/<THORN>/src/<FILE>
)
"""

f90_file_proc = """
add_custom_command(
    OUTPUT ${BUILD}/<THORN>/<FILE>
    COMMAND mkdir -p ${BUILD}/<THORN>
    COMMAND perl -p -e 's.//.CCTK_AUTOMATICALLY_GENERATED_CONCATENATION_PROTECTION.g' < ${ARRANGEMENTS}/<ARR>/<THORN>/src/<FILE> > ${BUILD}/<THORN>/<FILE>.tmp1
    COMMAND cpp -traditional  -D_OPENMP -I"/${ARRANGEMENTS}/<ARR>/<THORN>/src" \
#   -I"${CONFIG}/config-data" -I"${CONFIG}/bindings/include" \
#   -I"${CACTUS}/src/include" -I"${ARRANGEMENTS}" -I"${CONFIG}/bindings/Configuration/Thorns" \
#   -I"${CONFIG}/bindings/include/<THORN>" -I"${ARRANGEMENTS}/<ARR>/<THORN>/src" \
#   -I"${CONFIG}/bindings/include/<THORN>"  -DFCODE -DF90CODE < ${BUILD}/<THORN>/<FILE>.tmp1 > ${BUILD}/<THORN>/<FILE>.tmp2
    COMMAND mkFort.sh ${ARRANGEMENTS}/<ARR>/<THORN>/src/<FILE> ${BUILD}/<THORN>/<FILE>
    DEPENDS ${ARRANGEMENTS}/<ARR>/<THORN>/src/<FILE>
)
"""

c_file_proc = """
add_custom_command(
    OUTPUT ${BUILD}/<THORN>/<FILE>
    COMMAND mkdir -p ${BUILD}/<THORN> && ${PERL} -s ${C_FILE_PROCESSOR} -line_directives=yes -source_file_name=${ARRANGEMENTS}/<ARR>/<THORN>/src/<FILE> ${CONFIG}/config-data < ${ARRANGEMENTS}/<ARR>/<THORN>/src/<FILE> > ${BUILD}/<THORN>/<FILE>
    DEPENDS ${ARRANGEMENTS}/<ARR>/<THORN>/src/<FILE>
)
"""

c_file_proc2 = """
add_custom_command(
    OUTPUT ${BUILD}/Cactus/<FILE>
    COMMAND mkdir -p ${BUILD}/Cactus && ${PERL} -s ${C_FILE_PROCESSOR} -line_directives=yes -source_file_name=${CCTK_HOME}/src/<FILE> ${CONFIG}/config-data < ${CCTK_HOME}/src/<FILE> > ${BUILD}/Cactus/<FILE>
    DEPENDS ${CCTK_HOME}/src/<FILE>
)
"""

c_piraha = """

add_custom_command(
    OUTPUT ${BINDINGS}/include/ParGrammar.hh
    COMMAND mkdir -p ${BINDINGS}/include
	COMMAND ${PERL} ${CCTK_HOME}/src/piraha/make.hh.pl ${CCTK_HOME}/src/piraha/pegs/par.peg ${BINDINGS}/include/ParGrammar.hh
    DEPENDS ${CCTK_HOME}/src/piraha/pegs/par.peg
)

add_custom_target(generate_grammar
    DEPENDS ${BINDINGS}/include/ParGrammar.hh
)

add_dependencies(
    thorn_Cactus
    generate_grammar
)
"""


def has_fname(fname):
    with open(fname, "r") as fd:
        for line in fd.readlines():
            if "CCTK_FNAME" in line:
                return True
    return False


def trimlist(oldlist):
    used = set()
    newlist = list()
    for item in oldlist:
        if item in used:
            continue
        used.add(item)
        newlist.append(item)
    return newlist

searched_for_deps = dict()

def do_thorn(cactus:Cactus, thorn_name:str):
    global file_counter, file_transform_counter

    if thorn_name not in cactus.thorns:
        return
    thorn_info = cactus.thorns[thorn_name]
    arr, thorn_dir = thorn_info.arr, thorn_info.dir
    #print("do_thorn:", thorn)
    c_file_procs = ""
    buf2 = ""
    thorn_info = cactus.thorns[thorn_name]

    for src_file in thorn_info.src_files:
        if re.match(r'^.*\.(cxx|cpp|cc|c|C|F|F90)$', src_file):
            buf = c_file_proc
            buf = re.sub(r'<THORN>', thorn_name, buf)
            buf = re.sub(r'<ARR>', arr, buf)
            buf = re.sub(r'<FILE>', src_file, buf)
            #buf = re.sub(r'<INCS>',"\n".join(incs),buf)
            real_file = f"{thorn_dir}/src/{src_file}"
            if has_fname(real_file):
                buf2 += "    ${BUILD}/" + thorn_name + "/" + src_file + "\n"
                file_transform_counter += 1
            else:
                buf2 += "    ${CCTK_HOME}/" + real_file[len(cactus_dir) + 1:]
            file_counter += 1
            c_file_procs += buf

    includes:List[str] = list()
    for include in cactus.find_includes(thorn_name):
        includes.append(cactus.nice_path(include))

    if cactus.provides_functions(thorn_name):
        buf2 += f"    ${{BUILD}}/CactusBindings/Functions/{thorn_name}_Functions.c\n"

    buf = file_contents
    buf = re.sub(r'<THORN>', thorn_name, buf)
    buf = re.sub(r'<C_FILE_PROCS>', c_file_procs, buf)
    buf = re.sub(r'<FILES>', buf2, buf)
    buf = re.sub(r'<ARR>', arr, buf)
    buf = re.sub(r'<INC_DIRS>', '\n      '.join(includes), buf)

    with open(f"{config_dir}/CMake_{thorn_name}.txt", "w") as fd:
        print(buf, file=fd)


def do_flesh():
    c_file_procs = ""
    buf2 = ""
    thorn = "src"
    arr = "Cactus"
    #for src_file in os.listdir(f"{cactus}/src"):
    search = f"{cactus_dir}/src"
    print("Walking:",search)
    for dirpath, dirnames, filenames in os.walk(search):
        for src_file_top in filenames:
            if src_file_top in ["datestamp.c", "Generic.cc", "RecordImplementation.c", "regex.c"]:
                continue
            src_file = f"{dirpath}/{src_file_top}"[len(search) + 1:]
            #if re.match(r'^.*\.(cxx|cpp|cc|c|C|hxx|hh|hpp|h)$', src_file):
            if re.match(r'^.*\.(cxx|cpp|cc|c|C)$', src_file):
                buf = c_file_proc2
                buf = re.sub(r'<THORN>', "Cactus", buf)
                buf = re.sub(r'<ARR>', arr, buf)
                buf = re.sub(r'<FILE>', src_file, buf)
                buf2 += "    ${BUILD}/Cactus/" + src_file + "\n"
                print(">> SRC_FILE:", src_file)
                c_file_procs += buf
            else:
                print("SKIP>>", src_file)


    incs = cactus.find_includes( "Cactus")

    has_provides = False
    piraha_file = f"{config_dir}/piraha/{arr}/{thorn}/interface.cache"
    with open(piraha_file, "r") as fd:
        for line in fd.readlines():
            if ",PROVIDES_FUN" in line:
                has_provides = True
                buf2 += f"    ${{BUILD}}/CactusBindings/Functions/{thorn}_Functions.c\n"
                break

    buf = flesh_file_contents
    buf = re.sub(r'<THORN>', thorn, buf)
    buf = re.sub(r'<C_FILE_PROCS>', c_file_procs, buf)
    buf = re.sub(r'<FILES>', buf2, buf)
    buf = re.sub(r'<ARR>', arr, buf)
    buf = re.sub(r'<INCS_DIRS>', '\n      '.join(incs), buf)
    buf += c_piraha

    with open(f"{config_dir}/CMake_Cactus.txt", "w") as fd:
        print("# FLESH GENERATION", file=fd)
        print(buf, file=fd)

########### START ##############

argp, cactus_dir, config = make_argument_parser("CactusCmake")
cactus = Cactus(cactus_dir=cactus_dir, config=config)
config_dir = cactus.config_dir
print(f"Creating '{cactus.cactus_dir}/CMakeLists.txt' based on '{config_dir}' ...")

with open(f"{cactus_dir}/CMakeLists.txt", "w") as fd:
    print("cmake_minimum_required(VERSION 3.10)", file=fd)
    print("project(cactus_sim)", file=fd)
    print("""
set(MPI_HOME "/home/sbrandt/spack/var/spack/environments/cactus/.spack-env/view")
set(MPI_C_COMPILER "${MPI_HOME}/bin/mpicc")
set(MPI_CXX_COMPILER "${MPI_HOME}/bin/mpicxx")

find_package(MPI REQUIRED)
set(CONFIG_NAME "<config>")
set(CCTK_HOME "<cactus>")
set(CONFIGS "${CCTK_HOME}/configs")
set(CONFIG "${CONFIGS}/${CONFIG_NAME}")
set(PERL "/usr/bin/perl")
set(ARRANGEMENTS "${CCTK_HOME}/arrangements")
set(BUILD "${CONFIG}/build")
set(BINDINGS "${CONFIG}/bindings")
set(C_FILE_PROCESSOR "${CCTK_HOME}/lib/sbin/c_file_processor.pl")

set(CMAKE_CXX_LINK_GROUP_USING_cross_refs_SUPPORTED TRUE)
set(CMAKE_CXX_LINK_GROUP_USING_cross_refs
  "LINKER:--start-group"
  "LINKER:--end-group"
)

add_executable(cactus_<config>
    ${CCTK_HOME}/src/datestamp.c
    #${BINDINGS}/Variables/BindingsVariables.c
)
set_target_properties(cactus_<config> PROPERTIES LINKER_LANGUAGE CXX)

target_compile_options(cactus_<config> PUBLIC $<$<COMPILE_LANGUAGE:C>:-std=gnu99>)

target_compile_options(
    cactus_<config>
    PRIVATE
    -DCCODE
    -fopenmp
    -rdynamic
    #${MPI_C_COMPILE_OPTIONS}
)

target_link_options(
    cactus_<config>
    PRIVATE
    -fopenmp
    -rdynamic
    <LINK_OPTS>
)

target_include_directories(
    cactus_<config>
    PUBLIC
      ${CONFIG}/bindings/include/Cactus
      ${CONFIG}/config-data
      ${CONFIG}/bindings/include
      ${CONFIG}/build/Cactus/main
      ${CCTK_HOME}/src/include
      #${MPI_C_INCLUDE_DIRS}
)
""".replace("<cactus>", cactus_dir) \
          .replace("<config>", config) \
          .replace("<LINK_OPTS>", "\n".join(cactus.link_options)), file=fd)
    do_flesh()
    thorn_list:List[str] = list()
    with open(f"{cactus_dir}/configs/{config}/ThornList", "r") as fth:
        for line in fth.readlines():
            if g := re.match(r'^(\w+)/(\w+)', line):
                thorn = g.group(2)
                thorn_list.append(thorn)
    for thorn in thorn_list:
        do_thorn(cactus, thorn)
        print(f"include(configs/{config}/CMake_{thorn}.txt)", file=fd)
    print(f"include(configs/{config}/CMake_Cactus.txt)", file=fd)
    print(f"target_link_libraries(cactus_{config}", file=fd)
    for thorn in thorn_list:
        pass #print(f'    thorn_{thorn}', file=fd)
    #print(f"    thorn_Cactus", file=fd)
    thorn_list += ["Cactus"]
    #print("    ${MPI_C_LIBRARIES}",file=fd)
    #print("    adios2_fortran_mpi adios2_cxx11_mpi adios2_core_mpi adios2_fortran adios2_cxx11 adios2_c adios2_core",file=fd)
    #print("    /home/sbrandt/Cactus/configs/waveeqn/scratch/external/AMReX/lib/libamrex.a",file=fd)
    for lib in cactus.link_libraries:
        pass #print("   ", lib, file=fd)
    print("    \"$<LINK_GROUP:cross_refs,thorn_" + ",thorn_".join(thorn_list) + "," + ",".join(cactus.link_libraries) + ">\"", file=fd)
    print(")", file=fd)
#print("file_counter:", file_counter)
#print("file_transform_counter:", file_transform_counter)
#print("percent transformed: %.2f" % (100 * file_transform_counter / file_counter))
print("Done")
