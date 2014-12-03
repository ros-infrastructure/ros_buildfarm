#!/usr/bin/env sh

dot -Tpng devel_call_graph.dot > devel_call_graph.png
dot -Tpng release_call_graph.dot > release_call_graph.png
