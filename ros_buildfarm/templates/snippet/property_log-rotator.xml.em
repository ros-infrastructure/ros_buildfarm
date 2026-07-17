    <jenkins.model.BuildDiscarderProperty>
      <strategy class="hudson.tasks.LogRotator">
        <daysToKeep>@int(days_to_keep)</daysToKeep>
        <numToKeep>@int(num_to_keep)</numToKeep>
        <artifactDaysToKeep>-1</artifactDaysToKeep>
        <artifactNumToKeep>@(artifact_num_to_keep if 'artifact_num_to_keep' in vars() else -1)</artifactNumToKeep>
        <removeLastBuild>false</removeLastBuild>
      </strategy>
    </jenkins.model.BuildDiscarderProperty>
