# Copyright 2019 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class PlotConfig:

    def __init__(self, name, data):  # noqa: D107
        self.name = name

        assert 'master_csv_name' in data, \
            "Plot config for '%s' lacks required master CSV file name" % \
            self.name

        assert 'style' in data, \
            "Plot config for '%s' lacks required style selection" % \
            self.name

        self.title = None
        if 'title' in data:
            self.title = data['title']

        self.y_axis_label = None
        if 'y_axis_label' in data:
            self.y_axis_label = data['y_axis_label']

        self.master_csv_name = data['master_csv_name']

        self.style = data['style']
        assert self.style in (
            'area', 'bar', 'bar3d', 'line', 'lineSimple', 'line3d', 'stackedArea',
            'stackedBar', 'stackedBar3d', 'waterfall')

        self.y_axis_exclude_zero = bool(data.get('y_axis_exclude_zero', False))

        self.y_axis_minimum = data.get('y_axis_minimum', None)
        self.y_axis_maximum = data.get('y_axis_maximum', None)

        self.description = data.get('description', '')

        self.num_builds = data.get('num_builds', 0)
        assert isinstance(self.num_builds, int)

        self.data_series = []
        if 'data_series' in data:
            data_series_data = data['data_series']
            assert isinstance(data_series_data, list)
            for series_data in data_series_data:
                self.data_series.append(PlotDataSeries(name, series_data))


class PlotDataSeries:

    def __init__(self, name, data):  # noqa: D107
        self.name = name

        assert 'data_file' in data, \
            "Plot data series for '%s' lacks required data_file path" % \
            self.name

        assert 'data_type' in data, \
            "Plot data series for '%s' lacks required data_type selection" % \
            self.name

        assert 'selection_flag' in data, \
            "Plot data series for '%s' lacks required selection_flag value" % \
            self.name

        self.data_file = data['data_file']

        self.data_type = data['data_type']
        assert self.data_type in ('csv', 'xml', 'properties')

        self.selection_flag = data['selection_flag']
        assert self.selection_flag in (
            'OFF', 'INCLUDE_BY_STRING', 'EXCLUDE_BY_STRING',
            'INCLUDE_BY_COLUMN', 'EXCLUDE_BY_COLUMN')

        self.selection_value = None
        if 'selection_value' in data:
            self.selection_value = data['selection_value']

        self.url = None
        if 'url' in data:
            self.url = data['url']
