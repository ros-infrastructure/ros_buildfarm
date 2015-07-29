@[if 'sources' in locals()]@
@[if sources]@
WORKDIR @(ws)/src
@[for i, (source_name, source) in enumerate(sources.items())]@
RUN @(source['cmd']) @(source['repo']) @(source_name) --branch  @(source['branch']) @[if 'package' in source]@  \
    && curl @(source['package']) > @(ws)/src/@(source_name)/package.xml@
@[end if]
@[end for]@
@[end if]@
@[end if]@
