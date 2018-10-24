test_result_CMD="catkin_test_results $WORKSPACE/@workspace_path/test_results --all"
echo "Invoking: $test_result_CMD"
echo ""
if type "catkin_test_results" > /dev/null; then
  set +e
  $test_result_CMD
  test_result_RC=$?
  set -e
  if [ -n "$ABORT_ON_TEST_FAILURE" -a "$ABORT_ON_TEST_FAILURE" != "0" ]; then
    (exit $test_result_RC)
  fi
else
  echo "'catkin_test_results' not found on the PATH. Please install catkin and source the environment to output the test result summary."
  test_result_RC=0
fi

# for backward compatibility only
catkin_test_results_RC=$test_result_RC
