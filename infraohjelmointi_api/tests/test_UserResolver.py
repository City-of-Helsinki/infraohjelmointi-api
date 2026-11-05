"""The cached token-to-user resolver (utils/user_resolver.py)."""

import threading
import time
import uuid
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.test import SimpleTestCase, TestCase
from helusers.models import ADGroup, ADGroupMapping
from helusers.settings import api_token_auth_settings

from infraohjelmointi_api.models import User
from infraohjelmointi_api.utils import user_resolver


def token_payload(sub, ad_groups, **claims):
    return {
        "sub": sub,
        "given_name": "Testi",
        "family_name": "Käyttäjä",
        "email": "testi.kayttaja@example.com",
        "ad_groups": ad_groups,
        "exp": 2000000000,
        **claims,
    }


class UserResolverTests(TestCase):
    def setUp(self):
        user_resolver.clear()
        self.addCleanup(user_resolver.clear)
        self.sub = str(uuid.uuid4())
        self.planners = Group.objects.create(name="planners")
        self.coordinators = Group.objects.create(name="coordinators")
        ADGroupMapping.objects.create(
            ad_group=self.ad_group("sg_kymp_sso_io_ohjelmoijat"), group=self.planners
        )
        ADGroupMapping.objects.create(
            ad_group=self.ad_group("sg_kymp_sso_io_koordinaattorit"), group=self.coordinators
        )

    @staticmethod
    def ad_group(name):
        return ADGroup.objects.create(name=name, display_name=name)

    def test_is_the_configured_resolver(self):
        self.assertIs(api_token_auth_settings.USER_RESOLVER, user_resolver.resolve_user)

    def test_first_request_syncs_the_user_from_the_token(self):
        user = user_resolver.resolve_user(None, token_payload(self.sub, ["sg_kymp_sso_io_ohjelmoijat"]))

        self.assertEqual((user.uuid, user.first_name, user.email),
                         (uuid.UUID(self.sub), "Testi", "testi.kayttaja@example.com"))
        self.assertEqual(list(user.groups.all()), [self.planners])

    def test_later_requests_with_the_same_token_only_load_the_user(self):
        payload = token_payload(self.sub, ["sg_kymp_sso_io_ohjelmoijat"])
        first = user_resolver.resolve_user(None, payload)

        with self.assertNumQueries(1):
            again = user_resolver.resolve_user(None, dict(payload))

        self.assertEqual(again.pk, first.pk)

    def test_a_token_with_other_ad_groups_syncs_again(self):
        user_resolver.resolve_user(None, token_payload(self.sub, ["sg_kymp_sso_io_ohjelmoijat"]))

        user = user_resolver.resolve_user(None, token_payload(self.sub, ["sg_kymp_sso_io_koordinaattorit"]))

        self.assertEqual(list(user.groups.all()), [self.coordinators])

    def test_syncs_again_after_the_cache_period(self):
        payload = token_payload(self.sub, ["sg_kymp_sso_io_ohjelmoijat"])
        user_resolver.resolve_user(None, payload)
        # A mapping added in the database only (e.g. in the admin).
        ADGroupMapping.objects.create(
            ad_group=ADGroup.objects.get(name="sg_kymp_sso_io_ohjelmoijat"), group=self.coordinators
        )

        groups_while_cached = set(user_resolver.resolve_user(None, payload).groups.all())
        later = time.monotonic() + user_resolver.CACHE_SECONDS + 1
        with patch.object(user_resolver.time, "monotonic", return_value=later):
            groups_after = set(user_resolver.resolve_user(None, payload).groups.all())

        self.assertEqual(groups_while_cached, {self.planners})
        self.assertEqual(groups_after, {self.planners, self.coordinators})

    def test_a_deleted_user_is_synced_again(self):
        payload = token_payload(self.sub, ["sg_kymp_sso_io_ohjelmoijat"])
        User.objects.filter(pk=user_resolver.resolve_user(None, payload).pk).delete()

        user = user_resolver.resolve_user(None, payload)

        self.assertEqual(user.uuid, uuid.UUID(self.sub))

    def test_a_failed_sync_is_not_cached(self):
        payload = token_payload(self.sub, ["sg_kymp_sso_io_ohjelmoijat"])
        with patch.object(user_resolver, "sync_user", side_effect=ValueError("bad token")), \
                self.assertRaises(ValueError):
            user_resolver.resolve_user(None, payload)

        self.assertEqual(user_resolver.resolve_user(None, payload).uuid, uuid.UUID(self.sub))


class ParallelFirstRequestsTests(SimpleTestCase):
    def setUp(self):
        user_resolver.clear()
        self.addCleanup(user_resolver.clear)

    def test_parallel_first_requests_sync_once(self):
        """A page load's parallel requests wait for one sync instead of each
        syncing behind the user-row lock."""
        synced = []

        class SyncedUser:
            pk = 1

        def slow_sync(request, payload):
            synced.append(payload["sub"])
            time.sleep(0.2)
            return SyncedUser()

        results = []
        payload = token_payload(str(uuid.uuid4()), [])
        with patch.object(user_resolver, "sync_user", side_effect=slow_sync), \
                patch.object(user_resolver, "get_user_model") as get_user_model:
            get_user_model.return_value.objects.get.return_value = SyncedUser()
            threads = [
                threading.Thread(target=lambda: results.append(user_resolver.resolve_user(None, payload)))
                for _ in range(10)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        self.assertEqual(len(synced), 1)
        self.assertEqual(len(results), 10)
