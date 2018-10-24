import yaml
from ros_buildfarm.aggregate_status import get_status_description

def test_aggregate_status():
    D = yaml.load(open('test/aggregate_status_tests.yaml'))
    match = 0
    for i, case in enumerate(D['test_cases']):
        distro = case.get('distro', 'indigo')
        blacklist = set(map(tuple, case.get('blacklist', [])))
        status = get_status_description(case['build_status'], D['expected'][distro], blacklist)
        assert status == case['result']
        if status == case['result']:
            match += 1
        else:
            print('Failure in test case #{}: {} != {}'.format(i + 1, status, case['result']))
    print('{}/{} correct'.format(match, len(D['test_cases'])))


if __name__ == '__main__':
    test_aggregate_status()
