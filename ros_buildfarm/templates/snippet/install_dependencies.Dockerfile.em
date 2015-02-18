# for each dependency: echo version, apt-get update, apt-get install
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
max_lines = 80
fold_factor = 1.0 * len(dependencies) / max_lines
# can be zero if no folding is necessary
begin_entries_for_line = int(math.floor(fold_factor))
# can be zero if there are no dependencies
end_entries_for_line = int(math.ceil(fold_factor))
number_of_begin_blocks = int(round((end_entries_for_line - fold_factor) * max_lines))
switch_index = number_of_begin_blocks * begin_entries_for_line

def get_run_command(index, dependencies, dependency_versions):
    name = dependencies[index]
    return \
        ('echo "{name}: {version}" && ' +
         'python3 -u /tmp/wrapper_scripts/apt-get.py update-and-install -q -y -o Debug::pkgProblemResolver=yes {name}').format(
            name=name, version=dependency_versions[name])
}@
@[if fold_factor > 1]@
# to prevent exceeding the docker layer limit several lines have been folded
@[end if]@
@[if begin_entries_for_line]@
@[for i in range(0, switch_index, begin_entries_for_line)]@
@{
cmds = []
for j in range(begin_entries_for_line):
    cmds.append(get_run_command(i + j, dependencies, dependency_versions))
}@
RUN @(' && '.join(cmds))
@[end for]@
@[end if]@
@[if end_entries_for_line]@
@[for i in range(switch_index, len(dependencies), end_entries_for_line)]@
@{
cmds = []
for j in range(end_entries_for_line):
    cmds.append(get_run_command(i + j, dependencies, dependency_versions))
}@
RUN @(' && '.join(cmds))
@[end for]@
@[end if]@
