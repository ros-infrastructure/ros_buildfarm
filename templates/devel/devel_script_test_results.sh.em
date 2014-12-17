if type "catkin_test_results" > /dev/null; then
  set +e
  (set -x; catkin_test_results $WORKSPACE/@workspace_path/test_results --all)
  set -e
else
  echo "If 'catkin_test_results' would be available it would output a summary of all test results:"
  echo "    $ catkin_test_results $WORKSPACE/@workspace_path/test_results --all"
fi
