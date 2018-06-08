catkin_test_results_CMD="colcon test-result --build-base $WORKSPACE/@workspace_path/test_results --all"
echo "Invoking: $catkin_test_results_CMD"
echo ""
set +e
$catkin_test_results_CMD
catkin_test_results_RC=$?
echo "Test result return code: $catkin_test_results_RC"
set -e
if [ -n "$ABORT_ON_TEST_FAILURE" -a "$ABORT_ON_TEST_FAILURE" != "0" ]; then
  (exit $catkin_test_results_RC)
fi
