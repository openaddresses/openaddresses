import json
import os
import requests


def get_changed_files() -> []:
    """
    Get the list of changed files on the current PR.
    :return: A list of changed file names
    """
    pr_number = os.environ.get('GITHUB_REF').split("/")[2]

    url = f"https://api.github.com/repos/openaddresses/openaddresses/pulls/{pr_number}/files"
    resp = requests.get(url, timeout=5, headers={"User-Agent": "OpenAddresses CI"})
    resp.raise_for_status()

    changed_files = []
    for file in resp.json():
        changed_files.append(file["filename"])

    return changed_files


def get_source_at_version(filename, gitref):
    """
    Use the Github RAW API to get the source code at a specific commit
    :param filename: The filename to get
    :param gitref: The commit to get the file at
    :return: The parsed JSON from the file. None if the file doesn't exist.
    """
    url = f"https://raw.githubusercontent.com/openaddresses/openaddresses/{gitref}/{filename}"
    resp = requests.get(url, timeout=5, headers={"User-Agent": "OpenAddresses CI"})

    if resp.status_code == 404:
        return None
    else:
        resp.raise_for_status()

    return resp.json()


def main():
    commit = os.environ.get('GITHUB_SHA')

    # Get the list of changed sources on the PR we're running against
    changed_files = get_changed_files()

    # Check each changed source to see which layers need to be run
    sources_to_run = []
    for changed_file in changed_files:
        # Skip over files that aren't sources
        if not changed_file.startswith("sources/"):
            continue

        sources_on_master = {}
        source_on_master = get_source_at_version(changed_file, 'master') or {"layers": {}}
        layers_on_master = source_on_master.get("layers") or {}
        for layer_type, sources in layers_on_master.items():
            for source in sources:
                source["_layer"] = layer_type
                sources_on_master[f"{layer_type}-{source.get('name')}"] = source

        source_on_branch = get_source_at_version(changed_file, commit) or {"layers": {}}
        layers_on_branch = source_on_branch.get("layers") or {}
        for layer_type, sources in layers_on_branch.items():
            for source in sources:
                source["_layer"] = layer_type
                source_key = f"{layer_type}-{source.get('name')}"

                # Look for the source in the file from master
                source_on_master = sources_on_master.get(source_key)

                # If it's not there, then it's new and we should run it
                if not source_on_master:
                    sources_to_run.append((changed_file, layer_type, source["name"]))
                    continue

                # If it's there, only run it if it changed
                if json.dumps(source, sort_keys=True) != json.dumps(sources_on_master, sort_keys=True):
                    sources_to_run.append((changed_file, layer_type, source["name"]))
                    continue

    print("Should run sources:", sources_to_run)


if __name__ == '__main__':
    main()
