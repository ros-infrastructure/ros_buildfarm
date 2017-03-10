# run all build steps
@{
import os
import re
section_id = 0
}@
@[for i, script in enumerate(scripts)]@
echo "Build step @(i + 1)"
@[  for j, line in enumerate(script.splitlines())]@
@[    if os.environ.get('TRAVIS') == 'true']@
@[      if line.startswith('echo "# BEGIN SECTION: ')]@
@{section_id += 1}@
echo "travis_fold:start:devel-build-section@(section_id)"
@[      end if]@
@[    end if]@
@line
@[    if os.environ.get('TRAVIS') == 'true']@
@[      if line == 'echo "# END SECTION"']@
echo "travis_fold:end:devel-build-section@(section_id)"
@[      end if]@
@[    end if]@
@[  end for]@
echo ""

@[end for]@
