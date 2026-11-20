import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


BUILD_INPUTS_LABEL = "de.ddb.labs.ddbmeme.build-inputs"
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
IMAGE_REF = re.compile(r"[a-z0-9][a-z0-9._:/-]*(?::[a-zA-Z0-9_.-]+|@sha256:[0-9a-f]{64})")
FROM = re.compile(r"FROM\s+(?:--platform=\S+\s+)?(\S+)(?:\s+AS\s+(\S+))?", re.IGNORECASE)


def inspect(image, template, *, allow_missing=False):
    result = subprocess.run(
        ["docker", "buildx", "imagetools", "inspect", "--format", template, image],
        capture_output=True,
        encoding="utf-8",
    )
    if result.returncode == 0:
        return result.stdout

    error = result.stderr.strip()
    missing = f"{image.lower()}: not found" in error.lower() or "manifest unknown" in error.lower()
    if allow_missing and missing:
        return None
    raise SystemExit(error or f"Could not inspect {image}.")


def base_images(dockerfile):
    names = {}
    stages = {}
    runtime_base = None
    for line in dockerfile.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields or fields[0].upper() != "FROM":
            continue
        match = FROM.fullmatch(line.strip())
        if not match:
            raise SystemExit(f"Unsupported FROM instruction in {dockerfile}: {line}")
        name, alias = match.groups()
        if name.lower() in stages:
            runtime_base = stages[name.lower()]
        elif name.lower() == "scratch":
            runtime_base = None
        elif IMAGE_REF.fullmatch(name):
            names[name] = None
            runtime_base = name
        else:
            raise SystemExit(f"Use a literal tagged or digest-pinned base in {dockerfile}: {name}")
        if alias:
            stages[alias.lower()] = runtime_base

    if not names:
        raise SystemExit(f"No external base images found in {dockerfile}.")
    return names, runtime_base


def valid_digest(value, image):
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        raise SystemExit(f"Invalid manifest digest for {image}: {value}")
    return value


def platform_digest(image, platform):
    os_name, architecture = platform.split("/", maxsplit=1)
    manifest = json.loads(inspect(image, "{{json .Manifest}}"))
    if "manifests" in manifest:
        for entry in manifest["manifests"]:
            target = entry.get("platform") or {}
            if target.get("os") == os_name and target.get("architecture") == architecture:
                return valid_digest(entry.get("digest"), image)
    else:
        digest = valid_digest(manifest.get("digest"), image)
        config = json.loads(inspect(f"{image.split('@')[0]}@{digest}", "{{json .Image}}"))
        if config.get("os") == os_name and config.get("architecture") == architecture:
            return digest
    raise SystemExit(f"No {platform} manifest found for {image}.")


def reusable_digest(image, fingerprint):
    published = inspect(image, "{{json .}}", allow_missing=True)
    if published is None:
        return None

    details = json.loads(published)
    config = (details.get("image") or {}).get("config") or {}
    labels = config.get("Labels") or {}
    if labels.get(BUILD_INPUTS_LABEL) == fingerprint:
        return valid_digest(details["manifest"].get("digest"), image)
    return None


def main():
    parser = argparse.ArgumentParser(description="Resolve release build inputs for Docker Buildx.")
    parser.add_argument("dockerfile", type=Path)
    args = parser.parse_args()

    platform = os.environ["TARGET_PLATFORM"]
    tag = os.environ["RELEASE_TAG"]
    revision = os.environ["RELEASE_REVISION"]
    names, runtime = base_images(args.dockerfile)
    bases = {name: platform_digest(name, platform) for name in names}
    inputs = json.dumps([platform, tag, revision, bases], sort_keys=True).encode("utf-8")
    fingerprint = hashlib.sha256(inputs).hexdigest()
    image = f"{os.environ['IMAGE']}:{tag}"
    existing = reusable_digest(image, fingerprint)

    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
        if existing:
            print(f"Reusing {image}@{existing} with unchanged build inputs.")
            print(f"reusable_digest={existing}", file=output)
        else:
            print(f"Building {image}: the tag is missing or its build inputs changed.")
            print(f"base_name={runtime or ''}", file=output)
            print(f"base_digest={bases.get(runtime, '')}", file=output)
            print(f"fingerprint={fingerprint}", file=output)
            print("contexts<<BASE_IMAGES", file=output)
            for name, digest in bases.items():
                print(f"{name}=docker-image://{name.split('@')[0]}@{digest}", file=output)
            print("BASE_IMAGES", file=output)


if __name__ == "__main__":
    main()
