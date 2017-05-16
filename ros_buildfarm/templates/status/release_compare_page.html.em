<!DOCTYPE html>
<html>
<head>
  <title>@title - @start_time_local_str</title>
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>

  <script type="text/javascript" src="js/moment.min.js"></script>
  <script type="text/javascript" src="js/zepto.min.js"></script>
  <script type="text/javascript">
    window.META_COLUMNS = 2;
  </script>
  <script type="text/javascript" src="js/setup.js?@(resource_hashes['setup.js'])"></script>

  <link rel="stylesheet" type="text/css" href="css/status_page.css?@(resource_hashes['status_page.css'])" />
  <link rel="stylesheet" type="text/css" href="css/compare_page.css?@(resource_hashes['compare_page.css'])" />
</head>
<body>
  <script type="text/javascript">
    window.age_threshold_green = moment.duration(7, 'hours');
    window.body_ready_with_age(moment.duration(moment() - moment("@start_time", "X")));
  </script>
  <div class="top logo">
    <h1><img src="http://wiki.ros.org/custom/images/ros_org.png" alt="ROS.org" width="150" height="32" /></h1>
    <h2>@title</h2>
  </div>
  <div class="top search">
    <form action="?">
      <input type="text" name="q" id="q" title="A query string can contain multiple '+' separated parts which must all be satisfied. Each part can also be a RegExp (e.g. to combine two parts with 'OR': 'foo|bar'), but can't contain '+'." />
      <p>Quick filter:
        <a href="?q=" title="Show all packages">*</a>,
        <a href="?q=DIFF_PATCH" title="Filter packages which are only differ in the patch version">different patch version</a>,
        <a href="?q=DOWNGRADE_VERSION" title="Filter packages which disappear by a sync from shadow-fixed to public">downgrade</a>,
        <a href="?q=DIFF_BRANCH_SAME_VERSION" title="Filter packages which are are released from different branches but have same minor version">same version from different branches</a>
      </p>
      <p id="search-count"></p>
    </form>
  </div>
  <div class="top age">
    <p>This should show the age of the page...</p>
  </div>
  <table>
    <caption></caption>
    <thead>
      <tr>
        <th class="sortable"><div>Package</div></th>
        <th class="sortable"><div>Repo</div></th>
        <th class="sortable"><div>Maintainer</div></th>
@[for rosdistro_name in rosdistro_names]@
        <th><div>@(rosdistro_name.capitalize())</div></th>
@[end for]@
      </tr>
    </thead>
    <tbody>
      <script type="text/javascript">window.tbody_ready();</script>
@[for pkg_name in sorted(pkgs_data.keys())]@
      <tr>@[for cell in pkgs_data[pkg_name]]<td>@(cell)</td>@[end for]</tr>
@[end for]@
    </tbody>
  </table>
  <script type="text/javascript">window.body_done();</script>
</body>
</html>
