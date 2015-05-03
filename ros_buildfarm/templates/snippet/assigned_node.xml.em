  <assignedNode>@
@(node_label if node_label else 'buildslave') || @
@('_'.join(['', job_type, rosdistro_name, arch])) || @
@('_'.join(['', job_type, rosdistro_name])) || @
@('_'.join(['', job_type, arch])) @
</assignedNode>
