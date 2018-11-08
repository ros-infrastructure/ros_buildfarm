@[if build_tool == 'catkin_make_isolated']@
test_result_EXECUTABLE="catkin_test_results"
test_result_CMD="$test_result_EXECUTABLE $WORKSPACE/@workspace_path/test_results --all"
@[elif build_tool == 'colcon']@
test_result_EXECUTABLE="colcon"
test_result_CMD="$test_result_EXECUTABLE test-result --test-result-base $WORKSPACE/@workspace_path/test_results --all"
@[else]@
echo "Unsupported build tool: @build_tool"
(exit 1)
@[end if]@

if ! type "$test_result_EXECUTABLE" > /dev/null; then
  echo "'$test_result_EXECUTABLE' not found on the PATH. Please make sure the tool is installed and the environment is setup (if applicable) to output the test result summary."
  test_result_RC=0
@[if build_tool == 'colcon']@
elif ! $($test_result_EXECUTABLE test-result --help > /dev/null 2> /dev/null); then
  echo "'$test_result_EXECUTABLE test-result' not available. Please make sure the necessary extension is installed to output the test result summary."
  test_result_RC=0
@[end if]@
else
  echo "Invoking: $test_result_CMD"
  set +e
  $test_result_CMD
  test_result_RC=$?
  set -e
  if [ -n "$ABORT_ON_TEST_FAILURE" -a "$ABORT_ON_TEST_FAILURE" != "0" ]; then
    (exit $test_result_RC)
  fi
fi

# for backward compatibility only
catkin_test_results_RC=$test_result_RC
