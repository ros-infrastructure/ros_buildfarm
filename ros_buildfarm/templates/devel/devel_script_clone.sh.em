# list of repositories to clone
@[for repo_spec, _ in scms]@
# - @repo_spec.name (@repo_spec.type, @repo_spec.url, @repo_spec.version)"
@[end for]@

mkdir -p @workspace_path/src

@[for repo_spec, path in scms]@
if [ ! -d "@path" ]; then
@[if repo_spec.type == 'git']@
    (set -x; git clone --recurse-submodules -b @repo_spec.version @repo_spec.url @path)
    (set -x; git -C @path --no-pager log -n 1)
@[elif repo_spec.type == 'hg']@
    (set -x; hg clone -b @repo_spec.version @repo_spec.url @path)
    (set -x; hg --cwd @path log -l 1)
@[elif repo_spec.type == 'svn']@
    (set -x; svn checkout -r @repo_spec.version @repo_spec.url @path)
    (set -x; svn log -l 1 @path)
@[else]@
    echo "Unsupported repository type '@repo_spec.type' (@repo_spec.url)"
    exit 1
@[end if]@
else
    echo "Skip cloning '@repo_spec.name' as it already exists (@path)"
fi
echo ""

@[end for]@
