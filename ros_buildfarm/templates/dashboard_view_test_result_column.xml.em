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
    <hudson.views.BuildButtonColumn/>
    <jenkins.plugins.extracolumns.TestResultColumn plugin="extra-columns@@1.14">
      <testResultFormat>1</testResultFormat>
    </jenkins.plugins.extracolumns.TestResultColumn>
  </columns>
  <includeRegex>@
@[if include_regex]@
@include_regex@
@[end if]@
@ @ </includeRegex>
  <recurse>false</recurse>
  <useCssStyle>false</useCssStyle>
  <includeStdJobList>true</includeStdJobList>
  <leftPortletWidth>50%</leftPortletWidth>
  <rightPortletWidth>50%</rightPortletWidth>
  <leftPortlets/>
  <rightPortlets/>
  <topPortlets/>
  <bottomPortlets/>
</hudson.plugins.view.dashboard.Dashboard>
