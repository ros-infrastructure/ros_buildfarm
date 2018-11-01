    <jenkins.advancedqueue.priority.strategy.PriorityJobProperty plugin="PrioritySorter@@3.6.0">
      <useJobPriority>@('true' if priority != -1 else 'false')</useJobPriority>
      <priority>@int(priority)</priority>
    </jenkins.advancedqueue.priority.strategy.PriorityJobProperty>
