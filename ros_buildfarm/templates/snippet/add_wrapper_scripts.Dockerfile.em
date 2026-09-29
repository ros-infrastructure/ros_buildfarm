RUN mkdir /tmp/wrapper_scripts
@[for filename in sorted(wrapper_scripts.keys())]@
RUN cat << 'EOF' > /tmp/wrapper_scripts/@(filename)
@(wrapper_scripts[filename])
EOF
@[end for]@
