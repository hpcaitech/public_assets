from packaging import version


def has_larger_or_equal_cuda_version(ver1, ver2):
    def _parse_version(ver):
        if '.' in ver:
            major, minor = ver.split('.')
        else:
            if ver.startswith('1'):
                major = ver[:2]
                minor = ver[2:]
            elif ver.startswith(ver):
                major = ver[:1]
                minor = ver[1:]
            else:
                raise ValueError(f'{ver} is not valid cuda version')
        return major, minor

    ver1_major, ver1_minor = _parse_version(ver1)
    ver2_major, ver2_minor = _parse_version(ver2)

    if ver1_major > ver2_major:
        return True
    elif ver1_major == ver2_major:
        if ver1_minor > ver2_minor:
            return True
        elif ver1_minor == ver1_minor:
            return True
        else:
            return False
    else:
        return False

def has_larger_or_equal_torch_version(ver1, ver2):
    if version.parse(ver1) >= version.parse(ver2):
        return True
    else:
        return False