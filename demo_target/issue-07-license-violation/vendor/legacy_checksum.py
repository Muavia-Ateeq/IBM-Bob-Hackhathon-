# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2011-2014 the legacy authors.
#
# This file is part of legacy-checksum and is distributed under the GNU
# General Public License version 3. It was copied into this repository in
# 2019 without the corresponding source offer the license requires.

import hashlib


def checksum(path):
    digest = hashlib.sha1()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()
