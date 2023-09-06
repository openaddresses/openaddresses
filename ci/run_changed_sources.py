from collections import namedtuple
import csv
import json
import logging
import os
import sys

import boto3
import openaddr.process_one
import requests


def mkdir_p(path):
    """
    Make a directory, including any parent directories that don't exist.
    :param path: The path to create
    :return: None
    """
    os.makedirs(path, exist_ok=True)


def get_changed_files(pr_number: int) -> list:
    """
    Get the list of changed files on the current PR.
    :rtype: list
    :return: A list of changed file names
    """
    url = f"https://api.github.com/repos/openaddresses/openaddresses/pulls/{pr_number}/files"

    headers = {
        "User-Agent": "OpenAddresses CI",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if github_token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + github_token

    resp = requests.get(
        url,
        timeout=5,
        headers=headers,
    )
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

    headers = {
        "User-Agent": "OpenAddresses CI",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if github_token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + github_token

    resp = requests.get(
        url,
        timeout=5,
        headers=headers,
    )

    if resp.status_code == 404:
        return None
    else:
        resp.raise_for_status()

    return resp.json()


def main():
    commit = os.environ.get('GITHUB_SHA')
    pr_number = os.environ.get('GITHUB_REF').split("/")[2]
    r2_bucket = os.environ.get("R2_BUCKET")
    csv.field_size_limit(sys.maxsize)

    # Set up logging
    openaddr_logger = logging.getLogger('openaddr')
    openaddr_logger.setLevel(logging.DEBUG)
    handler1 = logging.StreamHandler()
    handler1.setLevel(logging.DEBUG)
    log_format = '%(asctime)s %(levelname)07s: %(message)s'
    handler1.setFormatter(logging.Formatter(log_format))
    openaddr_logger.addHandler(handler1)
    _L = openaddr_logger.getChild('ci')

    assert r2_bucket, "R2_BUCKET must be set"

    # Get the list of changed sources on the PR we're running against
    pr_number = int(os.environ.get('GITHUB_REF').split("/")[2])
    changed_files = get_changed_files(pr_number)

    # Check each changed source to see which layers need to be run
    sources_to_run = changed_sources(changed_files, commit)

    # If there aren't any sources to run, then we're done
    if not sources_to_run:
        _L.info("No sources to run")
        return

    # Run each source with openaddr-process-one
    for source in sources_to_run:
        _L.info(f"Running {source.filename} {source.layer} {source.name}")
        path_to_source = os.path.split(source.filename)[0].replace("sources/", "")
        output_dir = os.path.join("output", path_to_source)
        mkdir_p(output_dir)
        state_path = openaddr.process_one.process(
            source.filename,
            output_dir,
            layer=source.layer,
            layersource=source.name,
            do_preview=True,
            do_mbtiles=True,
            do_pmtiles=True,
            mapbox_key=os.environ.get('MAPBOX_KEY'),
        )
        _L.info(f"Finished running {source.filename} {source.layer} {source.name} to {output_dir}")

        # Don't try to read the state file if process_one failed
        if not state_path:
            continue

        # Read the state file so we can show debug info in the PR comment
        with open(state_path, "r") as f:
            source.state.update(json.load(f))

    # Upload the output files to R2
    s3 = boto3.client(
        's3',
        endpoint_url=os.environ.get("R2_ENDPOINT"),
        aws_access_key_id=os.environ.get("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("R2_SECRET_ACCESS_KEY"),
    )

    bucket_root = f"runs/gh-{commit[:7]}"
    for root, dirs, files in os.walk("output"):
        rel_root = os.path.relpath(root, "output")
        for file in files:
            r2_key = os.path.join(bucket_root, rel_root, file)
            local_filename = os.path.join(root, file)
            _L.info(f"Uploading {local_filename} to r2://{r2_bucket}/{r2_key}")
            s3.upload_file(local_filename, r2_bucket, r2_key)

    # Build a comment with links to the data in R2
    comment_body = "| Source | Result | Output |\n"
    comment_body += "| ------ | ------ | ------ |\n"
    for source in sources_to_run:
        source_root = source.filename.replace('sources/', '').replace('.json', '')
        url_root = f"https://pub-ef300f2557d1441981e249a936132155.r2.dev/{bucket_root}/{source_root}/{source.layer}"

        if not source.state:
            source_result = ":x: Failed"
        elif source.state.get("feat count", 0) <= 0:
            source_result = ":x: No features"
        elif source.state.get("skipped"):
            source_result = ":white_check_mark: Skipped"
        elif source.state.get("source problem"):
            source_result = ":x: Source problem"
        else:
            source_result = f":white_check_mark: {source.state.get('feat count')} features"

        comment_body += f"{source.filename}/{source.layer}/{source.name} | "
        comment_body += f"{source_result} |"
        comment_body += f"[Image]({url_root}/preview.png) / "
        comment_body += f"[Map](https://protomaps.github.io/PMTiles/?url={url_root}/slippymap.pmtiles) / "
        comment_body += f"[Log]({url_root}/output.txt)\n"

    # Post a comment to the PR with a link to the data in R2
    pr_url = f"https://api.github.com/repos/openaddresses/openaddresses/issues/{pr_number}/comments"
    resp = requests.post(
        pr_url,
        timeout=5,
        headers={
            "User-Agent": "OpenAddresses CI",
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + os.environ.get("GITHUB_TOKEN"),
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={
            "body": comment_body,
        }
    )
    if resp.status_code != 201:
        _L.warning(f"Couldn't post comment. Response was: {resp.text}")


SourceData = namedtuple("SourceData", ["filename", "layer", "name", "state"])


def changed_sources(changed_files, commit) -> list[SourceData]:
    """
    Given a list of changed files, return a list of sources that need to be run.
    :param changed_files:
    :param commit:
    :return:
    """

    sources_to_run = []
    for changed_file in changed_files:
        # Skip over files that aren't sources
        if not changed_file.startswith("sources/"):
            continue

        # Skip over files that aren't JSON
        if not changed_file.endswith(".json"):
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
                    sources_to_run.append(SourceData(
                        filename=changed_file,
                        layer=layer_type,
                        name=source["name"],
                        state={},
                    ))
                    continue

                # If it's there, only run it if it changed
                if json.dumps(source, sort_keys=True) != json.dumps(source_on_master, sort_keys=True):
                    sources_to_run.append(SourceData(
                        filename=changed_file,
                        layer=layer_type,
                        name=source["name"],
                        state={},
                    ))
                    continue

    return sources_to_run


if __name__ == '__main__':
    main()
