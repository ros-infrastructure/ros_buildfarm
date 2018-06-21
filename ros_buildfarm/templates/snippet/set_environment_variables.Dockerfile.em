@[for name, value in environment_variables.items()]@
ENV @(name)='@(value)'
@[end for]@
