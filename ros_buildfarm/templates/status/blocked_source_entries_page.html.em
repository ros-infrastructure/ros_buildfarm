<!DOCTYPE html>
<html>
<head>
  <title>@title - @start_time</title>
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>

  <script type="text/javascript" src="js/moment.min.js"></script>
  <script type="text/javascript" src="js/zepto.min.js"></script>
  <script type="text/javascript">
    window.META_COLUMNS = 8;
  </script>
  <script type="text/javascript" src="js/setup.js?@(resource_hashes['setup.js'])"></script>
  <script type="text/javascript">
    var QUERY_TRANSFORMS = {
      'id': 'id=".*"',
      'label': 'label=".*"',
    };

    function encoded_query_a_tag(query, title, content) {
      document.write('<a href="?q=' + encodeURIComponent(query) + '" title="' + title + '">' + content + "</a>")
    }
  </script>

  <link rel="stylesheet" type="text/css" href="css/status_page.css?@(resource_hashes['status_page.css'])" />
  <link rel="stylesheet" type="text/css" href="css/blocked_releases_page.css?@(resource_hashes['blocked_releases_page.css'])" />
</head>
<body>
@{
import time
}@
  <script type="text/javascript">
    window.age_threshold_green = moment.duration(7, 'hours');
    window.body_ready_with_age(moment.duration(moment() - moment("@(time.time())", "X")));
  </script>
  <div class="top logo">
    <h1><img src="http://wiki.ros.org/custom/images/ros_org.png" alt="ROS.org" width="150" height="32" /></h1>
    <h2>Repos blocked by other repos<br />@(rosdistro_name)</h2>
  </div>
  <div class="top search">
    <form action="?">
      <input type="text" name="q" id="q" title="A query string can contain multiple '+' separated parts which must all be satisfied. Each part can also be a RegExp (e.g. to combine two parts with 'OR': 'foo|bar'), but can't contain '+'." />
      <p>
        <a href="?q=" title="Show all repos">all</a>,
        <script language="JavaScript">encoded_query_a_tag('label="RELEASED"', "Repositories that have a source entry", "released")</script>,
        <script language="JavaScript">encoded_query_a_tag('label="UNRELEASED"', "Repositories that do not have a source entry", "unreleased")</script>,
        <script language="JavaScript">encoded_query_a_tag('label="BLOCKED"', "Repositories that are do not have a source entry because their dependencies do not have a source entry", "blocked")</script>,
        <script language="JavaScript">encoded_query_a_tag('label="UNBLOCKED"', "Repositories for which a source entry can be added", "releasable")</script>,
        <script language="JavaScript">encoded_query_a_tag('label="UNBLOCKED_BLOCKING"', "Repositories that could have a source entry and are blocking others from having a source entry", "releasable and blocking")</script>,
        <script language="JavaScript">encoded_query_a_tag('label="UNBLOCKED_UNBLOCKING"', "Repositories that could have a source entry and are not preventing others from having one", "releasable and not blocking")</script>,
        <script language="JavaScript">encoded_query_a_tag('id="metapackages"', "Repositories that are dependencies of the metapackages repository", "metapackages")</script>
      </p>
      <p id="search-count"></p>
    </form>
  </div>

  <div class="top age">
    <p></p>
  </div>

  <div class="table-div">
    <table>
      <thead>
        <tr>
          <!-- warning: if titles run onto two lines, first row of table data may be affected -->
          <th class="sortable"><div>Repository</div></th>
          <th class="sortable"><div>Has Source Entry?</div></th>
          <th class="sortable">
            <div title="Number of repositories without source entries that are directly blocking this one">
              # blocking source entry
            </div>
          </th>
          <th class="sortable">
            <div title="Repositories that are directly blocking this one">
              Blocking repos
            </div>
          </th>
          <th class="sortable">
            <div title="Maintainers of the repositories that are directly blocking this one">
              Maintainers of blocks
            </div>
          </th>
          <th class="sortable">
            <div title="Number of repositories that are directly or indirectly blocking this one">
              # recursively blocked
            </div>
          </th>
          <th class="sortable">
            <div title="Number of repositories that are being directly blocked by this one">
              # directly blocked
            </div>
          </th>
          <th class="sortable">
            <div title="Repositories that are being directly blocked by this one">
              Directly blocked repos
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        <!-- Originally sort the table by the repos with the most recursively blocked dependencies -->
        <script type="text/javascript">window.sort=6; window.reverse=1;</script>
        <script type="text/javascript">window.tbody_ready();</script>
@[for row in repos_data]@
        <tr>
@[  for col in [
      'name',
      'version',
      'num_repos_blocked_by',
      'repos_blocked_by',
      'maintainers_of_repos_blocked_by',
      'num_repos_recursively_blocked',
      'num_repos_blocked',
      'repos_blocked',
      ]]@
          <td @(' class="thincol"' if col in ['version',] or col.startswith('num') else '')>@(row[col])</td>
@[  end for]@
        </tr>
@[end for]@
      </tbody>
    </table>
  </div>
  <script type="text/javascript">window.body_done();</script>
</body>
</html>
