    <jenkins.advancedqueue.priority.strategy.PriorityJobProperty plugin="PrioritySorter@@5.2.0">
      <useJobPriority>@('true' if priority != -1 else 'false')</useJobPriority>
      <priority>@int(priority)</priority>
    </jenkins.advancedqueue.priority.strategy.PriorityJobProperty>
