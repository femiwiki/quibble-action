# A script to resolve dependencies of MediaWiki extension for Quibble test
import os
import sys
import yaml

# parameter_functions for https://raw.githubusercontent.com/wikimedia/integration-config/master/zuul/parameter_functions.py
from parameter_functions import dependencies, get_dependencies

# Get dependency file path from argument
dependencies_file = sys.argv[1]

recurse = True  # Default to recursion
if len(sys.argv) >= 3 and sys.argv[2] == '--no-recurse':
    recurse = False

# Add dependencies of target extension
with open(dependencies_file, 'r') as f:
    dependencies['ext'] = yaml.load(f, Loader=yaml.SafeLoader)

# Define rules for exclusions and inclusions
branch_rules = {
    'REL1_42': {
        'exclude': {
            'CommunityConfiguration': 'Fails without CommunityConfigurationExample on REL1_42',
            'CommunityConfigurationExample': 'Does not exist on REL1_42',
        },
    },
    'only': {
        'DiscussionTools': {
            'branches': ['master'],
            'reason': 'Inconsistently failing',
        },
    },
}

# Resolve dependencies
resolved_dependencies = []
for d in get_dependencies('ext', dependencies, recurse):
    repo = ''
    branch = ''
    if d in dependencies['ext']:
        if 'repo' in dependencies['ext'][d] and dependencies['ext'][d]['repo'] != 'auto':
            repo = '|' + dependencies['ext'][d]['repo']
        if 'branch' in dependencies['ext'][d] and dependencies['ext'][d]['branch'] != 'auto':
            branch = dependencies['ext'][d]['branch']

    if branch:
        branch = '|' + branch

    d = 'mediawiki/extensions/' + d
    d = d.replace('/extensions/skins/', '/skins/')
    d = d + repo + branch
    resolved_dependencies.append(d)

print('\n'.join(resolved_dependencies))
