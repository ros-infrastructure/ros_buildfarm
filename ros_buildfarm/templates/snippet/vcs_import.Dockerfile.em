@[if 'vcs' in locals()]@
@[if vcs]@
WORKDIR @(ws)
@[for i, (imports_name, imports) in enumerate(vcs.items())]@
RUN wget @(imports['repos']) \
    && vcs import @(ws) < @(imports_name).repos
@[end for]@
@[end if]@
@[end if]@
