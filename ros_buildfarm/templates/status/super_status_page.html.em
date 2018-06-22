<!DOCTYPE html>
<html>
<head>
  <title>@title - @start_time_local_str</title>
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>

  <script type="text/javascript" src="js/moment.min.js"></script>
  <script type="text/javascript" src="js/zepto.min.js"></script>
  </script>
  <script src="http://code.jquery.com/jquery-2.0.3.min.js"></script>
  <script src="http://culmat.github.io/jsTreeTable/treeTable.js"></script>
  <script type="text/javascript" src="js/setup.js"></script>

  <link rel="stylesheet" type="text/css" href="css/status_page.css" />
  <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.1.0/css/all.css" integrity="sha384-lKuwvrZot6UHsBSfcMvOkWwlCMgc0TaWr+30HWe3a4ltaBwTZhyTEggF5tJv8tbt" crossorigin="anonymous">
  <style>
  tbody tr td span { display: inline; }
  .organization { font-size: 130%; }
  .repo { font-size: 115%; }
  .status {
    font-weight: 900;
    font-family: "Font Awesome 5 Free";
    font-style: normal;
    font-size: 150%;
  }
  .status:before {
    content: "\f0a3";
  }
  .released:before {
    content: "\f14a";
    color: green;
  }
  .waiting:before {
    content: "\f055";
    color: blue;
  }
  .source:before {
    content: "\f1c9";
    color: red;
  }
  .mixed:before {
    content: "\f24d";
    color: gray;
  }
  .broken:before {
    content: "\f057";
    color: red
  }
  .complicated:before {
    content: "\f1d0";
    font-family: "Font Awesome 5 Brands";
    color: red
  }
  </style>
</head>
@{
def status_cell(status):
    if not status:
        return '<td></td>'
    css_class = ''
    if status == 'released':
        css_class = status
    elif 'waiting' in status:
        css_class = 'waiting'
    elif 'source' in status:
        css_class = 'source'
    elif status == 'mixed':
        css_class = 'mixed'
    elif 'build' in status:
        css_class = 'broken'
    elif 'complicated' in status:
        css_class = 'complicated'
    return '<td class="status {}" title="{}"></td>'.format(css_class, status)
}
<body>
  <script type="text/javascript">
    window.body_ready_with_age(moment.duration(moment() - moment("@start_time", "X")));
  </script>
  <div class="top logo search">
    <h1><img src="http://wiki.ros.org/custom/images/ros_org.png" alt="ROS.org" width="150" height="32" /></h1>
    <h2>@title</h2>
  </div>
  <div class="top age">
    <p>This should show the age of the page...</p>
  </div>
  <table id="table">
    <caption></caption>
    <thead>
    <tr><th>Name
    @[for distro in distros]@
    <th><div>@distro</div>
    @[end for]@
    </thead>
    <tbody>
    @[for org in sorted(super_status, key=lambda d: d.lower())]@
    <tr data-tt-id="O@org" data-tt-level="1"><td class="organization">@org
        @[for distro in distros]@
        @status_cell(super_status[org]['status'].get(distro))
        @[end for]@
    </tr>
        @[for repo in sorted(super_status[org]['repos'])]@
        <tr data-tt-id="R@repo" data-tt-parent-id="O@org" data-tt-level="2"><td class="repo">@repo
            @[for distro in distros]@
            @status_cell(super_status[org]['repos'][repo]['status'].get(distro))
            @[end for]@
        </tr>
            @[for pkg in sorted(super_status[org]['repos'][repo]['pkgs'])]@
            <tr data-tt-id="@pkg" data-tt-parent-id="R@repo" data-tt-level="3"><td class="pkg">@pkg
                @[for distro in distros]@
                @status_cell(super_status[org]['repos'][repo]['pkgs'][pkg]['status'].get(distro))
                @[end for]@
            </tr>
            @[end for]@
        @[end for]@
    @[end for]@
    </tbody>

    <script type="text/javascript">
        com_github_culmat_jsTreeTable.register(this);
        table = treeTable($('#table'));
        table.expandLevel(0);
        window.tbody_ready();
    </script>
  </table>
  <script type="text/javascript">window.body_done();</script>
</body>
</html>
