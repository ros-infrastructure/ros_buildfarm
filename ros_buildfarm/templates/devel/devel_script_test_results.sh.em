catkin_test_results_CMD="catkin_test_results $WORKSPACE/@workspace_path/test_results --all"
echo "Invoking: $catkin_test_results_CMD"
echo ""
if type "catkin_test_results" > /dev/null; then
  set +e
  $catkin_test_results_CMD
  catkin_test_results_RC=$?
  set -e
  if [ -n "$ABORT_ON_TEST_FAILURE" -a "$ABORT_ON_TEST_FAILURE" != "0" ]; then
    (exit $catkin_test_results_RC)
  fi
else
  echo "'catkin_test_results' not found on the PATH. Please install catkin and source the environment to output the test result summary."
  catkin_test_results_RC=0
fi
