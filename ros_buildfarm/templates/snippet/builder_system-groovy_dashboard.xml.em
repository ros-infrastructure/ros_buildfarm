@(SNIPPET(
    'builder_system-groovy',
    command=
"""import hudson.model.Result
import jenkins.model.Jenkins

view_stats = [:]
for (v in Jenkins.instance.views) {
  success = 0
  unstable = 0
  failure = 0
  aborted = 0
  not_built = 0
  disabled = 0
  ignored = 0
  for (p in v.items) {
    if (!p.hasProperty("lastBuild")) {
      // non-job item, e.g. a folder
      ignored++
      continue
    }
    if (p.isDisabled()) {
      disabled++
      continue
    }
    def lb = p.lastBuild
    if (!lb) {
      // job has never been built
      not_built++
      continue
    }
    def r = lb.result
    def pb = lb
    while (!r) {
      pb = pb.previousBuild
      if (!pb) {
        // no finished build yet
        break
      }
      r = pb.result
    }
    if (r == Result.SUCCESS) {
      success++
    } else if (r == Result.UNSTABLE) {
      unstable++
    } else if (r == Result.FAILURE) {
      failure++
    } else if (r == Result.ABORTED) {
      aborted++
    } else if (!r) {
      not_built++
    } else if (r == Result.NOT_BUILT) {
      // this should never happen for the result of a build
      assert false
    } else {
      // unknown result value
      println("View '" + v.viewName + "'' job '" + p.name + "'' has unknown result: " + r)
      assert false
    }
  }
  view_stat = ["count": v.items.size, "success": success, "unstable": unstable, "failure": failure, "aborted": aborted, "not_built": not_built, "disabled": disabled, "ignored": ignored]
  if (v.items.size != success + unstable + failure + aborted + not_built + disabled + ignored) {
    assert false, "View '" + v.viewName + "' has inconsistent stats: " + v.items.size + " != " + success + " + " + unstable + " + " + failure + " + " + aborted + " + " + not_built + " + " + disabled + " + " + ignored
  }
  view_stats[v.viewName] = view_stat
}

view_max_length = 0
max_count = 0
for (v in view_stats) {
  // determine maximum length of view name
  view_max_length = Math.max(view_max_length, v.key.length())
  // compute percentages
  count = v.value["count"]
  max_count = Math.max(max_count, count)
  // get fixed array of keys, which does not update when we add more keys
  columns = v.value.keySet().toArray()
  for (c in columns) {
    if (c == "count") continue
    percent = v.value[c] * 100
    if (count != 0) percent /= count
    percent = Math.floor(percent * 100) / 100
    v.value[c + "_percent"] = String.format("%.2f", percent)
  }
}
max_count_length = String.format("%d", max_count).length()
//println("view length: " + view_max_length)
//println("max count length: " + max_count_length)
//println("Stats: " + view_stats)

count_label = "count"
max_count_column_length = Math.max(max_count_length, count_label.length())

// output ascii table

// table header
println("")
columns = ["success", "unstable", "failure", "aborted", "not_built", "disabled"]
// first columns is: view_max_length + 2 whitespaces
print(" " * view_max_length + "  ")
// second columns is: 2 whitespaces + max_count_column_length + 2 whitespaces
print("|  " + count_label + " " * (max_count_column_length - count_label.length()) + "  ")
for (c in columns) {
  // other columns are: 2 whitespaces + max_count_length + whitespace + parenthesis open + percentage (xxx.xx) + whitespace + percent sign + parenthesis close + 2 whitespaces
  // which equals to: 2 whitespaces + max_count_length + 11 characters + 2 whitespaces
  padding = max_count_length + 11 - c.length()
  print("|  " + " " * Math.floor(padding / 2) + c + " " * Math.ceil(padding / 2) + "  ")
}
println("")

// table separator line
print("-" * (view_max_length + 2))
print("+" + "-" * (max_count_column_length + 4))
for (c in columns) {
  print("+" + "-" * (max_count_length + 15))
}
println("")

// table rows
for (v in view_stats) {
  // first column
  print(v.key + " " * (view_max_length - v.key.length() + 2))
  // second column
  print("|" + "  ")
  value = v.value["count"]
  print(" " * (max_count_column_length - ("" + value).length()) + value)
  print("  ")
  // other columns
  for (c in columns) {
    print("|" + "  ")
    value = v.value[c]
    print(" " * (max_count_length - ("" + value).length()) + value)
    print(" ")
    percent = v.value[c + "_percent"]
    print(" " * (6 - percent.length()))
    print("(")
    print(percent)
    print(" %)")
    print("  ")
  }
  println()
}
""",
    script_file=None,
))@
