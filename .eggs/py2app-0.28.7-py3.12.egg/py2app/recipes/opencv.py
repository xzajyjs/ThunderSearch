def check(cmd, mf):
    m = mf.findNode("cv2")
    if m is None or m.filename is None:
        return None

    return {"includes": ["numpy"]}
