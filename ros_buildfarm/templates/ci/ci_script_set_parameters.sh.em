# set default parameter values
@[for key, val in sorted(parameters.items())]@
@key="@val.replace('"', '\\"')"
@[end for]@
