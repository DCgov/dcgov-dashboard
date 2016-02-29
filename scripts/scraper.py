import requests
import json
from jsonschema import validate
from settings import ACCESS_TOKEN


def format_activity(data):
    return [d['total'] for d in data]


def format_teams(data):
    return [d['name'] for d in data]


def format_timeline(data):
    return {
        "pushed_at": format_date(data['pushed_at']),
        "created_at": format_date(data['created_at']),
        "updated_at": format_date(data['updated_at'])
    }


def format_date(datestring):
    return datestring.split('T')[0]


def github_api_items(full_name):
    print(full_name)
    return [
        {
            "name": "activity",
            "url": 'https://api.github.com/repos/{}/stats/commit_activity'.format(full_name),
            "formatter": format_activity
        },
        {
            "name": "teams",
            "url": 'https://api.github.com/repos/{}/teams'.format(full_name),
            "formatter": format_teams
        },
        {
            "name": "languages",
            "url": 'https://api.github.com/repos/{}/languages'.format(full_name),
            "formatter": ""
        },
        {
            "name": "timeline",
            "url": 'https://api.github.com/repos/{}'.format(full_name),
            "formatter": format_timeline
        }
    ]


def github_metadata(full_name, github_headers):
    github = {}
    items = github_api_items(full_name)
    for item in items:
        response = requests.get(item['url'], headers=github_headers)
        data = response.json()
        if item['formatter']:
            data = item['formatter'](data)
        github[item['name']] = data
    return github


def civicjson_metadata(full_name, default_branch, schema):
    url = 'https://raw.githubusercontent.com/{0}/{1}/civic.json'.format(full_name, default_branch)
    response = requests.get(url)
    try:
        data = response.json()
        data['name'] = data['name'].lower()
        data['tags'] = sorted(data['tags'], key=lambda s: s.lower())
        validate(data, schema)
        return data
    except:
        return None


if __name__ == '__main__':
    meta_all = []
    github_headers = {'Authorization': 'token {}'.format(ACCESS_TOKEN)}
    schema = requests.get('https://raw.githubusercontent.com/DCgov/civic.json/master/schema.json').json()
    repos = requests.get('https://api.github.com/orgs/dcgov/repos').json()
    for repo in repos:
        meta_project = civicjson_metadata(repo['full_name'], repo['default_branch'], schema)
        if meta_project:
            meta_project['github'] = github_metadata(repo['full_name'], github_headers)
            meta_all.append(meta_project)

    with open('_data/projects.json', 'w') as outfile:
        json.dump(meta_all, outfile, indent=4)
