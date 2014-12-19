# run all build steps
@[for i, script in enumerate(scripts)]@
echo "Build step @(i + 1)"
# output the commands executed in this block
(set -x; @script)
echo ""

@[end for]@
