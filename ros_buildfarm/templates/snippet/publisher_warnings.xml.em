    <hudson.plugins.warnings.WarningsPublisher plugin="warnings@@4.63">
      <healthy/>
      <unHealthy/>
      <thresholdLimit>low</thresholdLimit>
      <pluginName>[WARNINGS] </pluginName>
      <defaultEncoding/>
      <canRunOnFailed>false</canRunOnFailed>
      <usePreviousBuildAsReference>false</usePreviousBuildAsReference>
      <useStableBuildAsReference>false</useStableBuildAsReference>
      <useDeltaValues>false</useDeltaValues>
      <thresholds plugin="analysis-core@@1.92">
@[if unstable_threshold != '']@
        <unstableTotalAll>@unstable_threshold</unstableTotalAll>
@[else]@
        <unstableTotalAll/>
@[end if]@
        <unstableTotalHigh/>
        <unstableTotalNormal/>
        <unstableTotalLow/>
        <unstableNewAll/>
        <unstableNewHigh/>
        <unstableNewNormal/>
        <unstableNewLow/>
        <failedTotalAll/>
        <failedTotalHigh/>
        <failedTotalNormal/>
        <failedTotalLow/>
        <failedNewAll/>
        <failedNewHigh/>
        <failedNewNormal/>
        <failedNewLow/>
      </thresholds>
      <shouldDetectModules>false</shouldDetectModules>
      <dontComputeNew>true</dontComputeNew>
      <doNotResolveRelativePaths>true</doNotResolveRelativePaths>
      <includePattern/>
      <excludePattern/>
      <messagesPattern/>
      <categoriesPattern/>
      <parserConfigurations/>
      <consoleParsers>
        <hudson.plugins.warnings.ConsoleParser>
          <parserName>CMake</parserName>
        </hudson.plugins.warnings.ConsoleParser>
        <hudson.plugins.warnings.ConsoleParser>
          <parserName>GNU C Compiler 4 (gcc)</parserName>
        </hudson.plugins.warnings.ConsoleParser>
      </consoleParsers>
    </hudson.plugins.warnings.WarningsPublisher>
