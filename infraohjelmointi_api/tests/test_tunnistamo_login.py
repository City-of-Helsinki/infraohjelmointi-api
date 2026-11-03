"""Helsinki Login (Tunnistamo) to the Django admin goes through helusers'
TunnistamoOIDCAuth on top of social-auth-core.

social-auth-core 6.1+ calls ``get_remote_jwks_keys(uri)`` while helusers 1.3
overrides it as ``get_remote_jwks_keys(self)``, so every login callback raised a
TypeError while validating the id_token. requirements.txt keeps
social-auth-app-django on 6.1 (social-auth-core < 6) for that reason.
"""

import json
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from helusers.tunnistamo_oidc import TunnistamoOIDCAuth
from social_django.utils import load_strategy


class TunnistamoSigningKeysTests(SimpleTestCase):
    def test_id_token_signing_keys_can_be_fetched(self):
        """The id_token check starts from get_jwks_keys, as during a login callback."""
        backend = TunnistamoOIDCAuth(load_strategy())
        jwks = {"keys": [{"kid": "key-1", "kty": "RSA", "n": "AQAB", "e": "AQAB"}]}

        # social-auth-core fetches the keys with request() or get_json() depending
        # on the version; answer both without a network call.
        response = Mock(text=json.dumps(jwks), json=Mock(return_value=jwks))
        with patch.object(TunnistamoOIDCAuth, "jwks_uri", return_value="https://login.example/jwks"), \
                patch.object(TunnistamoOIDCAuth, "request", return_value=response), \
                patch.object(TunnistamoOIDCAuth, "get_json", return_value=jwks):
            keys = backend.get_jwks_keys()

        self.assertEqual([key["kid"] for key in keys], ["key-1"])
        # helusers' override ran: it defaults a missing alg to RS256.
        self.assertEqual(keys[0]["alg"], "RS256")
