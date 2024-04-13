def _emulate_shell_environ():
    import os
    import sys
    import time

    if sys.version_info[0] > 2:
        env = os.environb
    else:
        env = os.environ

    split_char = b"="

    # Start 'login -qf $LOGIN' in a pseudo-tty. The pseudo-tty
    # is required to get the right behavior from the shell, without
    # a tty the shell won't properly initialize the environment.
    #
    # NOTE: The code is very carefull w.r.t. getting the login
    # name, the application shouldn't crash when the shell information
    # cannot be retrieved
    try:
        login = os.getlogin()
        if login == "root":
            # For some reason os.getlogin() returns
            # "root" for user sessions on Catalina.
            try:
                login = os.environ["LOGNAME"]
            except KeyError:
                login = None
    except AttributeError:
        try:
            login = os.environ["LOGNAME"]
        except KeyError:
            login = None

    if login is None:
        return

    master, slave = os.openpty()
    pid = os.fork()

    if pid == 0:
        # Child
        os.close(master)
        os.setsid()
        os.dup2(slave, 0)
        os.dup2(slave, 1)
        os.dup2(slave, 2)
        os.execv("/usr/bin/login", ["login", "-qf", login])
        os._exit(42)

    else:
        # Parent
        os.close(slave)
        # Echo markers around the actual output of env, that makes it
        # easier to find the real data between other data printed
        # by the shell.
        os.write(master, b'echo "---------";env;echo "-----------"\r\n')
        os.write(master, b"exit\r\n")
        time.sleep(1)

        data = []
        b = os.read(master, 2048)
        while b:
            data.append(b)
            b = os.read(master, 2048)
        data = b"".join(data)
        os.waitpid(pid, 0)

    in_data = False
    for ln in data.splitlines():
        if not in_data:
            if ln.strip().startswith(b"--------"):
                in_data = True
            continue

        if ln.startswith(b"--------"):
            break

        try:
            key, value = ln.rstrip().split(split_char, 1)
        except Exception:
            pass

        else:
            env[key] = value


_emulate_shell_environ()
