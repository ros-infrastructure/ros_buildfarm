<hudson.plugins.view.dashboard.Dashboard plugin="dashboard-view@@2.9.4">
  <name>@view_name</name>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
  <filterExecutors>false</filterExecutors>
  <filterQueue>true</filterQueue>
  <properties class="hudson.model.View$PropertyList"/>
  <jobNames>
    <comparator class="hudson.util.CaseInsensitiveComparator"/>
  </jobNames>
  <jobFilters/>
  <columns>
    <hudson.views.StatusColumn/>
    <hudson.views.WeatherColumn/>
    <hudson.views.JobColumn/>
    <hudson.views.LastSuccessColumn/>
    <hudson.views.LastFailureColumn/>
    <hudson.views.LastDurationColumn/>
    <jenkins.plugins.extracolumns.BuildDescriptionColumn plugin="extra-columns@@1.15">
      <columnWidth>80</columnWidth>
      <forceWidth>true</forceWidth>
    </jenkins.plugins.extracolumns.BuildDescriptionColumn>
    <hudson.views.BuildButtonColumn/>
    <jenkins.plugins.extracolumns.TestResultColumn plugin="extra-columns@@1.15">
      <testResultFormat>1</testResultFormat>
    </jenkins.plugins.extracolumns.TestResultColumn>
  </columns>
  <includeRegex>@(include_regex if include_regex else '')</includeRegex>
  <recurse>false</recurse>
  <useCssStyle>false</useCssStyle>
  <includeStdJobList>false</includeStdJobList>
  <leftPortletWidth>50%</leftPortletWidth>
  <rightPortletWidth>50%</rightPortletWidth>
  <leftPortlets>
    <hudson.plugins.view.dashboard.stats.StatBuilds>
      <id>dashboard_portlet_5357</id>
      <name>Build statistics</name>
    </hudson.plugins.view.dashboard.stats.StatBuilds>
  </leftPortlets>
  <rightPortlets>
    <hudson.plugins.view.dashboard.test.TestTrendChart>
      <id>dashboard_portlet_6555</id>
      <name>Test Trend Chart</name>
      <graphWidth>500</graphWidth>
      <graphHeight>220</graphHeight>
      <dateRange>0</dateRange>
      <dateShift>0</dateShift>
      <displayStatus>ALL</displayStatus>
    </hudson.plugins.view.dashboard.test.TestTrendChart>
  </rightPortlets>
  <topPortlets/>
  <bottomPortlets>
    <hudson.plugins.view.dashboard.core.HudsonStdJobsPortlet>
      <id>dashboard_portlet_14122</id>
      <name>Jenkins jobs list</name>
    </hudson.plugins.view.dashboard.core.HudsonStdJobsPortlet>
  </bottomPortlets>
</hudson.plugins.view.dashboard.Dashboard>
