@[if repo_spec.type == 'git']@
@(SNIPPET(
    'scm_git',
    url=repo_spec.url,
    branch_name=repo_spec.version,
    relative_target_dir=path,
    refspec=None,
    git_ssh_credential_id=git_ssh_credential_id,
))@
@[elif repo_spec.type == 'hg']@
@(SNIPPET(
    'scm_hg',
    source=repo_spec.url,
    branch=repo_spec.version,
    subdir=path,
))@
@[elif repo_spec.type == 'svn']@
@(SNIPPET(
    'scm_svn',
    remote=repo_spec.url,
    local=path,
))@
@[else]@
@{assert False, "Unsupported repository type '%s'" % repo_spec.type}@
@[end if]@
