RUN mkdir /tmp/wrapper_scripts
@[for filename in sorted(wrapper_scripts.keys())]@
RUN echo "@('\\n'.join(wrapper_scripts[filename].replace('\\', '\\\\\\\\').replace('"', '\\"').splitlines()))" > /tmp/wrapper_scripts/@(filename)
@[end for]@
