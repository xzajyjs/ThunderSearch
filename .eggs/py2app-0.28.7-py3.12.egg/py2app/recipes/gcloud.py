def check(cmd, mf):
    m = mf.findNode("gcloud")
    if m is None or m.filename is None:
        return None

    # Dependency in package metadata, but
    # no runtime dependency. Explicity include
    # to ensure that the package metadata for
    # googleapis_common_protos is included.
    return {"includes": ["google.api"]}
