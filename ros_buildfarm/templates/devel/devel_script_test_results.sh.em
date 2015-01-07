catkin_test_results_CMD="catkin_test_results $WORKSPACE/@workspace_path/test_results --all"
echo "Invoking: $catkin_test_results_CMD"
echo ""
if type "catkin_test_results" > /dev/null; then
  set +e
  $catkin_test_results_CMD
  set -e
else
  echo "'catkin_test_results' not found on the PATH. Please install catkin and source the environment to output the test result summary."
fi
