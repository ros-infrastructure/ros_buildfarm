from enum import Enum

from rosdistro import DistributionCache
from rosdistro import DistributionFile
from rosdistro import DocBuildFile
from rosdistro import get_distribution_file
from rosdistro import get_distribution_cache
from rosdistro import get_doc_build_files
from rosdistro import get_index
from rosdistro import get_release_build_files
from rosdistro import get_source_build_files
from rosdistro import Index
from rosdistro import ReleaseBuildFile
from rosdistro import SourceBuildFile
from rosdistro.package import Package
from rosdistro.repository import Repository

from ros_buildfarm.common import OSArchTarget

from ros_buildfarm.common import OSTarget
from ros_buildfarm.common import JobValidationError
from ros_buildfarm.git import get_ros_buildfarm_url
from ros_buildfarm.jenkins import connect


class BuildType(Enum):
    """
    Represents the different build file types (release, source, doc).
    """
    release = 1
    source = 2
    doc = 3


class BuildConfiguration(object):
    """
    Represents the basic configuration for a build.

    Most of the time, this will be read from the command line
    using L{from_args}.
    """

    def __init__(self, rosdistro_index_url, rosdistro_name,
                 release_build_name,
                 source_build_name,
                 doc_build_name,
                 append_timestamp=False,
                 ros_buildfarm_url=None):
        self.rosdistro_index_url = rosdistro_index_url
        self.rosdistro_name = rosdistro_name
        self.source_build_name = source_build_name
        self.release_build_name = release_build_name
        self.doc_build_name = doc_build_name
        self.append_timestamp = append_timestamp
        self.ros_buildfarm_url = get_ros_buildfarm_url() \
            if ros_buildfarm_url is None \
            else ros_buildfarm_url


    @staticmethod
    def from_args(args):
        """
        Load the build configuration from the command line args object.
        @rtype: BuildConfiguration
        """
        return BuildConfiguration(
            args.rosdistro_index_url,
            args.rosdistro_name,
            source_build_name=getattr(args, 'source_build_name', None),
            release_build_name=getattr(args, 'release_build_name', None),
            doc_build_name=getattr(args, 'doc_build_name', None),
            append_timestamp=getattr(args, 'append_timestamp', None)
        )

    def resolve(self, build_type, override=None):
        """
        Load the actual build configuration from the index file.
        @type build_type: BuildType
        @type override: BaseBuildConfiguration
        @rtype: SourceBuildConfiguration
        """
        index = None
        dist_file = None
        build_file = None
        dist_cache = None

        if override is not None:
            index = override.index
            dist_file = override.dist_file
            build_file = override.build_file
            dist_cache = override.dist_cache

        if index is None:
            index = get_index(self.rosdistro_index_url)

        if dist_file is None:
            dist_file = get_distribution_file(index, self.rosdistro_name)

        if build_type is BuildType.source:
            return self._resolve_source_build(index, build_file,
                                              dist_file, dist_cache)
        elif build_type is BuildType.release:
            return self._resolve_release_build(index, build_file,
                                               dist_file, dist_cache)
        elif build_type is BuildType.doc:
            return self._resolve_doc_build(index, build_file,
                                           dist_file, dist_cache)
        else:
            assert False, "Unknown build type %s" % build_type

    def _resolve_source_build(self, index, build_file, dist_file, dist_cache):
        if build_file is None:
            build_files = get_source_build_files(index, self.rosdistro_name)
            build_file = build_files[self.release_build_name]

        if dist_cache is None and build_file.notify_maintainers:
            dist_cache = get_distribution_cache(index, self.rosdistro_name)

        return SourceBuildConfiguration(self, index=index, dist_file=dist_file,
                                        build_file=build_file, dist_cache=dist_cache)

    def _resolve_release_build(self, index, build_file, dist_file, dist_cache):
        if build_file is None:
            build_files = get_release_build_files(index, self.rosdistro_name)
            build_file = build_files[self.release_build_name]

        if dist_cache is None:
            if build_file.notify_maintainers or build_file.abi_incompatibility_assumed:
                dist_cache = get_distribution_cache(index, self.rosdistro_name)

        return ReleaseBuildConfiguration(self, index=index, dist_file=dist_file,
                                         build_file=build_file, dist_cache=dist_cache)

    def _resolve_doc_build(self, index, build_file, dist_file, dist_cache):
        if build_file is None:
            build_files = get_doc_build_files(index, self.rosdistro_name)
            build_file = build_files[self.release_build_name]

        # TODO
        # if dist_cache is None:
        # if build_file.notify_maintainers or build_file.abi_incompatibility_assumed:
        # dist_cache = get_distribution_cache(index, self.rosdistro_name)

        return DocBuildConfiguration(self, index=index, dist_file=dist_file,
                                     build_file=build_file, dist_cache=dist_cache)


class BaseBuildConfiguration(object):
    """
    Represents the basic configuration for a build, after resolving the index url.
    """

    def __init__(self, base: BuildConfiguration,
                 index: Index,
                 dist_file: DistributionFile,
                 build_file: ReleaseBuildFile,
                 dist_cache: DistributionCache):
        self.base = base
        self.index = index
        self.dist_file = dist_file
        self.build_file = build_file
        self.dist_cache = dist_cache
        self.__pkg_names = None

    def verify_is_in_list(self, desc, item, list):
        if item not in list:
            raise JobValidationError("Invalid %s '%s' " % (desc, item) +
                                     'choose one of the following: ' +
                                     ', '.join(sorted(list)))

    ### Jenkins handling

    def connect_to_jenkins(self):
        """@rtype: jenkinsapi.jenkins.Jenkins"""
        return connect(self.build_file.jenkins_url)

    ### Target OS handling

    def get_target_os(self):
        """@rtype: list[OSTarget]"""
        targets = []
        for os_name in self.build_file.get_target_os_names():
            for os_code_name in self.build_file.get_target_os_code_names(os_name):
                targets.append(OSTarget(os_name, os_code_name))
        return targets

    def get_os_architecture_targets(self):
        """@rtype: list[OSArchTarget]"""
        targets = []
        for os_target in self.get_target_os():
            for arch in self.get_target_architectures_by_os(os_target):
                targets.append(OSArchTarget(os_target, arch))
        return targets

    def get_target_architectures_by_os(self, os_target: OSTarget):
        """@rtype: list[str]"""
        return self.build_file.get_target_arches(os_target.os_name,
                                                 os_target.os_code_name)

    def get_filtered_target_architectures_by_os(self, os_target: OSTarget, print_skipped=True):
        """@rtype: list[str]"""
        arches = []
        for arch in self.get_target_architectures_by_os(os_target):
            # TODO support for non amd64 arch missing
            if arch not in ['amd64']:
                if print_skipped:
                    print('Skipping arch:', arch)
                continue
            arches.append(arch)
        return arches

    def verify_target_os(self, os_target: OSTarget):
        """
        Verify that this build configuration contains instructions for the specified OS.
        """
        self.verify_is_in_list("OS name", os_target.os_name,
                               self.build_file.get_target_os_names())

        self.verify_is_in_list("OS code name", os_target.os_code_name,
                               self.build_file.get_target_os_code_names(os_target.os_name))

    def verify_target_os_architecture(self, os_arch_target: OSArchTarget):
        """
        Verify that this build configuration contains instructions
        for the specified OS/architecture combination.
        """
        self.verify_target_os(os_arch_target.os_target)

        self.verify_is_in_list("architecture", os_arch_target.arch,
                               self.get_target_architectures_by_os(
                                   os_arch_target.arch))

    def get_target_configuration(self, target):
        os_name = target.os_name
        os_code_name = target.os_code_name
        arch = getattr(target, 'arch', None)
        return self.build_file.get_target_configuration(
            os_name, os_code_name, arch)

    ### Package name handling

    def get_package_names(self):
        if self.__pkg_names is None:
            pkg_names = self.dist_file.release_packages.keys()
            pkg_names = self.build_file.filter_packages(pkg_names)
            self.__pkg_names = pkg_names
        return self.__pkg_names

    def verify_contains_package(self, pkg_name: str):
        self.verify_is_in_list("package name", pkg_name, self.get_package_names())

    def get_package_info(self, pkg_name: str):
        """@rtype: PackageInfo"""
        pkg = self.dist_file.release_packages[pkg_name]
        repo_name = pkg.repository_name
        repo = self.dist_file.repositories[repo_name]
        return PackageInfo(pkg, repo)

    def get_direct_dependencies(self, pkg_name: str):
        """@rtype: list[str]"""
        from catkin_pkg.package import parse_package_string

        assert self.dist_cache is not None
        if pkg_name not in self.dist_cache.release_package_xmls:
            return None
        pkg_xml = self.dist_cache.release_package_xmls[pkg_name]
        pkg = parse_package_string(pkg_xml)
        depends = set([
            d.name for d in (
                pkg.buildtool_depends +
                pkg.build_depends +
                pkg.buildtool_export_depends +
                pkg.build_export_depends +
                pkg.exec_depends +
                pkg.test_depends)
            if d.name in self.get_package_names()])
        return depends

    ### Notification handling

    def get_maintainer_emails_to_notify(self, repo_name: str):
        if self.build_file.notify_maintainers:
            return self.get_maintainer_emails(repo_name)
        else:
            return set([])

    def get_maintainer_emails(self, repo_name: str):
        maintainer_emails = set([])
        if self.dist_cache and repo_name in self.dist_cache.distribution_file.repositories:
            from catkin_pkg.package import parse_package_string
            # add maintainers listed in latest release to recipients
            repo = self.dist_cache.distribution_file.repositories[repo_name]
            if repo.release_repository:
                for pkg_name in repo.release_repository.package_names:
                    if pkg_name not in self.dist_cache.release_package_xmls:
                        continue
                    pkg_xml = self.dist_cache.release_package_xmls[pkg_name]
                    pkg = parse_package_string(pkg_xml)
                    for m in pkg.maintainers:
                        maintainer_emails.add(m.email)
        return maintainer_emails


class SourceBuildConfiguration(BaseBuildConfiguration):
    def __init__(self,
                 base: BuildConfiguration,
                 index: Index,
                 dist_file: DistributionFile,
                 build_file: SourceBuildFile,
                 dist_cache: DistributionCache):
        super().__init__(base, index, dist_file, build_file, dist_cache)

    def get_filtered_repositories(self):
        repo_names = self.dist_file.repositories.keys()
        repo_names = self.build_file.filter_repositories(repo_names)
        return repo_names

    def verify_repository_name(self, repo_name: str):
        self.verify_is_in_list("repository name", repo_name, self.get_filtered_repositories())


class ReleaseBuildConfiguration(BaseBuildConfiguration):
    def __init__(self,
                 base: BuildConfiguration,
                 index: Index,
                 dist_file: DistributionFile,
                 build_file: ReleaseBuildFile,
                 dist_cache: DistributionCache):
        super().__init__(base, index, dist_file, build_file, dist_cache)


class DocBuildConfiguration(BaseBuildConfiguration):
    def __init__(self,
                 base: BuildConfiguration,
                 index: Index,
                 dist_file: DistributionFile,
                 build_file: DocBuildFile,
                 dist_cache: DistributionCache):
        super().__init__(base, index, dist_file, build_file, dist_cache)


class PackageInfo:
    def __init__(self, pkg: Package, repo: Repository):
        self.pkg = pkg
        self.repo = repo

    @property
    def pkg_name(self):
        return self.pkg.name

    @property
    def repo_name(self):
        return self.repo.name

    @property
    def release_repository(self):
        return self.repo.release_repository
