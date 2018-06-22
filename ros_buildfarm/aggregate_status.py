import re
import collections

CANDIDATES = ['build', 'test', 'main']
VERSION_PATTERN = re.compile('([\d\-\.]+)\w+.*')


def map_value_matches(M, key, value_list):
    """
       Convenience function for repeated operation to check if the
       dictionary M's value for the given key (which is a set)
       matches the set version of the list of values passed in.
    """
    return M[key] == set(value_list)


def some_map_value_matches(M, value_list):
    """
       Returns true if some value in M
       matches the set version of the list of values passed in.
    """
    values = set(value_list)
    for key in M.keys():
        if M[key] == values:
            return True
    return False


def some_other_value_matches(M, value_list, exclude):
    """
       Returns true if some value in M except the one with key=exclude
       matches the set version of the list of values passed in.
    """
    values = set(value_list)
    for key in M.keys():
        if key != exclude and M[key] == values:
            return True
    return False

def no_overlap_in_values_and_none(M):
    if None not in M:
        return False
    # Assume M has two key/value pairs
    values0, values1 = M.values()
    return len(values0.intersection(values1)) == 0

def get_distro_status(D, expected, blacklist, candidates=CANDIDATES, skip_source=False, debug=False):
    """
     D is a recursive structure that map a specific build i.e.
      (os_name, os_flavor, cpu, candidate) to a version number
      If the version number is not present, then it is an error, i.e. version_number = None

     expected is the values of (os_name, os_flavor, cpu) that we expect to see
       (this is constant across all packages)

     blacklist is a set of (os_name, os_flavor, cpu) that we don't expect to see
       (specific to this package)
    """

    # The first thing we do is reverse the mapping

    # version_map maps version to a list of (os_name, os_flavor, cpu, candidate)
    version_map = collections.defaultdict(list)

    # the following four structures map the version to either the os_name, os_flavor, etc
    os_map = collections.defaultdict(set)
    flavor_map = collections.defaultdict(set)
    cpu_map = collections.defaultdict(set)
    candidate_map = collections.defaultdict(set)

    # this maps the version to the os_flavor + cpu
    combo_map = collections.defaultdict(set)

    # build the reversed maps
    for os_name in expected:
        os_d = D.get(os_name, {})
        for os_flavor in expected[os_name]:
            fl_d = os_d.get(os_flavor, {})
            for cpu in expected[os_name][os_flavor]:
                if skip_source and cpu == 'source':
                    continue
                cpu_d = fl_d.get(cpu, {})
                for candidate in candidates:
                    version = None
                    if candidate in cpu_d:
                        version = VERSION_PATTERN.match(cpu_d[candidate]).group(1)
                    elif (os_name, os_flavor, cpu) in blacklist:
                        continue
                    os_map[version].add(os_name)
                    flavor_map[version].add(os_flavor)
                    cpu_map[version].add(cpu)
                    candidate_map[version].add(candidate)
                    combo_map[version].add(os_flavor + '/' + cpu)
                    version_map[version].append((os_name, os_flavor, cpu, candidate))

    # If there's only one version across all builds (and nothing is missing), then
    # this package is completely synced and released
    if len(version_map) == 1:
        return 'released'

    # If there are two different versions available
    if len(version_map) == 2:
        if map_value_matches(candidate_map, None, ['main']):
            # one version for build/test, and all the main builds are None
            # this package hasn't been released yet, but it builds fine otherwise
            return 'waiting for new release'
        elif some_map_value_matches(candidate_map, ['main']):
            # still one version for build/test, and some other version for main
            return 'waiting for re-release'

        if some_map_value_matches(cpu_map, ['source']):
            cpu_version0, cpu_version1 = sorted(cpu_map.keys())
            # these versions could be (None, version) or (old_version, new_version)

            if cpu_version0 is None:
                return 'source builds, binary doesn\'t'
            elif map_value_matches(cpu_map, cpu_version0, ['source']):
                # the source is the only thing that builds for the new version
                return 'source builds, binary doesn\'t'

        if no_overlap_in_values_and_none(flavor_map):
            # if the thing that separates the working builds and nonworking builds is the os_flavor
            return 'does not build on ' + ', '.join(sorted(flavor_map[None]))
        elif no_overlap_in_values_and_none(cpu_map):
            return 'does not build on ' + ', '.join(sorted(cpu_map[None]))
        elif no_overlap_in_values_and_none(combo_map):
            return 'does not build on ' + ', '.join(sorted(combo_map[None]))

    # If there are three different versions availble
    elif len(version_map) == 3:
        if map_value_matches(candidate_map, None, ['main']) and some_other_value_matches(candidate_map, ['main'], None):
            # This package builds fine in build/test, and has two different versions
            # in main, including None, then been released for some builds but not others
            return 'waiting for new/re-release'

    if None in version_map:
        # if some version is breaking (and doesn't match the above patterns)
        # gather all the flavor/cpu combos that are breaking
        DX = set([(os_flavor, cpu) for os_name, os_flavor, cpu, candidate in version_map[None]])
        if len(DX) == 1:
            os_flavor, cpu = list(DX)[0]
            return "does not build on %s/%s" % (os_flavor, cpu)

    if candidates == CANDIDATES:
        sub_candidates = CANDIDATES[:-1]  # skip main
        status = get_distro_status(D, expected, blacklist, sub_candidates)
        if status and status != 'released':
            return status

        status = get_distro_status(D, expected, blacklist, sub_candidates, True)
        if status and status != 'released':
            return 'binary: ' + status

    if not debug:
        return
    print('{} versions ({})'.format(len(version_map), ', '.join(map(str, sorted(version_map)))))
    for name, M in [('os', os_map), ('flavor', flavor_map), ('cpu', cpu_map), ('candidate', candidate_map),
                    ('combo', combo_map)]:
        print(name)
        for version, values in M.iteritems():
            print('\t{}: {}'.format(version, ', '.join(values)))

    for version, M in sorted(version_map.items()):
        print(version, len(M))
        if version is None:
            print(M)
    print()

def get_aggregate_status(D, expected, pkg_name=None, blacklist={}, debug=False):
    per_distro = {}
    for distro in sorted(D):
        if distro == 'maintainers':
            continue
        status = get_distro_status(D[distro]['build_status'],
                                   expected[distro],
                                   blacklist.get(pkg_name, {}).get(distro, set()),
                                   debug=debug)
        if status is None:
            status = 'complicated'
        per_distro[distro] = status

    return per_distro
