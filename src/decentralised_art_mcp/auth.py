from __future__ import annotations

import os
from typing import Optional

from eth_account import Account


def load_account(private_key: Optional[str] = None):
    key = private_key or os.getenv("PRIVATE_KEY")
    if not key:
        raise RuntimeError("Missing private key. Pass private_key explicitly or set PRIVATE_KEY.")
    return Account.from_key(key)
