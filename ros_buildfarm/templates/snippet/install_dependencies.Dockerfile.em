# for each dependency: echo version, apt update, apt install, apt clean
@{
# in order to not exceed the maximum layer limit of docker
# fold lines if they would exceed the limit
#
# for N dependencies and M maximum lines
# there needs to be an average of N / M entries per line
# the first block of lines will contain floor(N / M) entries
# the second block of lines will contain ceil(N / M) entries
#
# if there are more dependencies then the limit
# the folding will generate exactly the number of lines as allowed by the limit
import math
# folding all dependencies into a single line
# improves the performance of individual jobs especially with many dependencies
# but makes it very unlikely to share layers across different jobs
max_lines = 1
fold_factor = 1.0 * len(dependencies) / max_lines
# can be zero if no folding is necessary
begin_entries_for_line = int(math.floor(fold_factor))
# can be zero if there are no dependencies
end_entries_for_line = int(math.ceil(fold_factor))
number_of_begin_blocks = int(round((end_entries_for_line - fold_factor) * max_lines))
switch_index = number_of_begin_blocks * begin_entries_for_line

def get_run_command(indices, dependencies, dependency_versions):
    cmds = []
    names = []
    for index in indices:
      name = dependencies[index]
      cmds.append('echo "{name}: {version}"'.format(name=name, version=dependency_versions[name]))
      names.append(name)
    cmds.append('python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y -o Debug::pkgProblemResolver=yes {names}'.format(names=' '.join(names)))
    return ' && '.join(cmds)
}@
@[if fold_factor > 1]@
# to prevent exceeding the docker layer limit several lines have been folded
@[end if]@
@[if begin_entries_for_line]@
@[for i in range(0, switch_index, begin_entries_for_line)]@
@{
indices = []
for j in range(begin_entries_for_line):
    indices.append(i + j)
}@
RUN @(get_run_command(indices, dependencies, dependency_versions))
@[end for]@
@[end if]@
@[if end_entries_for_line]@
@[for i in range(switch_index, len(dependencies), end_entries_for_line)]@
@{
indices = []
for j in range(end_entries_for_line):
    indices.append(i + j)
}@
RUN @(get_run_command(indices, dependencies, dependency_versions))
@[end for]@
@[end if]@
