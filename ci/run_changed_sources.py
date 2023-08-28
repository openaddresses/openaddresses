import boto3
import json
import os
import requests


def mkdir_p(path):
    """
    Make a directory, including any parent directories that don't exist.
    :param path: The path to create
    :return: None
    """
    os.makedirs(path, exist_ok=True)


def get_changed_files() -> []:
    """
    Get the list of changed files on the current PR.
    :return: A list of changed file names
    """
    pr_number = os.environ.get('GITHUB_REF').split("/")[2]

    url = f"https://api.github.com/repos/openaddresses/openaddresses/pulls/{pr_number}/files"
    resp = requests.get(
        url,
        timeout=5,
        headers={
            "User-Agent": "OpenAddresses CI",
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + os.environ.get("GITHUB_TOKEN"),
            "X-GitHub-Api-Version": "2022-11-28",
        },
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
    resp = requests.get(
        url,
        timeout=5,
        headers={
            "User-Agent": "OpenAddresses CI",
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + os.environ.get("GITHUB_TOKEN"),
            "X-GitHub-Api-Version": "2022-11-28",
        },
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

    assert r2_bucket, "R2_BUCKET must be set"

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

    # Run each source with openaddr-process-one
    for source in sources_to_run:
        print(f"Running {source[0]} {source[1]} {source[2]}")
        path_to_source = os.path.split(source[0])[0].replace("sources/", "")
        output_dir = os.path.join("output", path_to_source)
        mkdir_p(output_dir)
        os.system(f"openaddr-process-one {source[0]} {output_dir} "
                  f"--layer {source[1]} "
                  f"--layersource {source[2]} "
                  f"--render-preview "
                  f"--mapbox-key {os.environ.get('MAPBOX_KEY')}")

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
            print(f"Uploading {local_filename} to r2://{r2_bucket}/{r2_key}")
            s3.upload_file(local_filename, r2_bucket, r2_key)

    # Build a comment with links to the data in R2
    comment_body = f"Data for this PR is available at:\n\n"
    comment_body += "Source |     |    \n"
    comment_body += "------ | --- | ---\n"
    for source in sources_to_run:
        comment_body += f"[{source[1]}/{source[2]}](https://pub-ef300f2557d1441981e249a936132155.r2.dev/{bucket_root}/{source[0]}/{source[1]}/{source[2]}) | "
        comment_body += f"[Preview](https://pub-ef300f2557d1441981e249a936132155.r2.dev/{bucket_root}/{source[0]}/{source[1]}/{source[2]}/preview.png) | "
        comment_body += f"[Log](https://pub-ef300f2557d1441981e249a936132155.r2.dev/{bucket_root}/{source[0]}/{source[1]}/{source[2]}/output.txt)\n"

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
    resp.raise_for_status()


if __name__ == '__main__':
    main()
