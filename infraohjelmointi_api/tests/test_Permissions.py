from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from helusers.models import ADGroup
from infraohjelmointi_api.models import (
    ProjectProgrammer, ProjectClass, Project, ProjectPhase, ClassProgrammerAssignment, Note, ProjectGroup
)
from infraohjelmointi_api.permissions import (
    IsClassProgrammer,
    IsPlanner,
    IsProjectManager,
    IsPlannerOfProjectAreas,
)
from infraohjelmointi_api.views import BaseViewSet
from unittest.mock import Mock

User = get_user_model()


class RestrictedProgrammerPermissionsTestCase(TestCase):
    """Test restricted permissions for class programmers"""

    def setUp(self):
        from django.conf import settings
        restricted_group_name = getattr(settings, 'RESTRICTED_PROGRAMMER_AD_GROUP', 'sg_kymp_sso_io_rajoitetut_ohjelmoijat')

        self.restricted_programmer_group = ADGroup.objects.create(
            name=restricted_group_name,
            display_name='Restricted Programmers'
        )
        self.coordinator_group = ADGroup.objects.create(
            name='sg_kymp_sso_io_koordinaattorit',
            display_name='Coordinators'
        )

        # Create test users
        self.programmer_user = User.objects.create_user(
            username='john.doe@test.fi',
            email='john.doe@test.fi'
        )
        self.programmer_user.ad_groups.add(self.restricted_programmer_group)

        self.other_user = User.objects.create_user(
            username='other.user@test.fi',
            email='other.user@test.fi'
        )
        self.other_user.ad_groups.add(self.restricted_programmer_group)

        self.coordinator_user = User.objects.create_user(
            username='coordinator@test.fi',
            email='coordinator@test.fi'
        )
        self.coordinator_user.ad_groups.add(self.coordinator_group)

        # Create ProjectClasses
        self.bridge_class = ProjectClass.objects.create(
            name='B Siltojen peruskorjaukset',
            path='8 03 Kadut ja liikenneväylät/8 03 01 Uudisrakentaminen ja perusparantaminen sekä muut investoinnit, Kaupunkiympäristölautakunnan käytettäväksi/8 03 01 02 Perusparantaminen ja liikennejärjestelyt/B Siltojen peruskorjaukset'
        )
        self.snow_class = ProjectClass.objects.create(
            name='B Lumenvastaanottopaikat ja hiekkasiilot',
            path='8 03 Kadut ja liikenneväylät/8 03 01 Uudisrakentaminen ja perusparantaminen sekä muut investoinnit, Kaupunkiympäristölautakunnan käytettäväksi/8 03 01 03 Muut investoinnit/B Lumenvastaanottopaikat ja hiekkasiilot'
        )
        self.parks_804_class = ProjectClass.objects.create(
            name='Uudet puistot',
            path='8 04 Puistot ja viheralueet/8 04 01 Uudet puistot'
        )

        # Create ProjectProgrammer assignments
        self.programmer_assignment = ProjectProgrammer.objects.create(
            firstName='John',
            lastName='Doe',
            person=None
        )
        self.bridge_class.defaultProgrammer = self.programmer_assignment
        self.bridge_class.save()

        # Create test projects
        phase = ProjectPhase.objects.first()
        if not phase:
            phase = ProjectPhase.objects.create(value='planning', index=1)

        self.bridge_project = Project.objects.create(
            name='Test Bridge Project',
            description='Test bridge project description',
            projectClass=self.bridge_class,
            phase=phase
        )
        self.snow_project = Project.objects.create(
            name='Test Snow Project',
            description='Test snow project description',
            projectClass=self.snow_class,
            phase=phase
        )
        self.parks_804_project = Project.objects.create(
            name='Test Parks 804 Project',
            description='Test parks 804 project description',
            projectClass=self.parks_804_class,
            phase=phase
        )



    def test_direct_assignment_grants_access(self):
        """IO-756: Test that ClassProgrammerAssignment grants access"""
        # Assign programmer_user directly to snow_class
        ClassProgrammerAssignment.objects.create(
            user=self.programmer_user,
            project_class=self.snow_class
        )

        factory = APIRequestFactory()
        request = factory.patch('/projects/1/', {})
        request.user = self.programmer_user
        request.data = {}

        permission = IsClassProgrammer()
        view = Mock()
        view.action = 'partial_update'

        # User has direct assignment to snow_class
        has_permission = permission.has_object_permission(
            request, view, self.snow_project
        )
        self.assertTrue(has_permission)

    def test_no_assignment_denies_access(self):
        """IO-756: Test that user without assignment is denied"""
        factory = APIRequestFactory()
        request = factory.patch('/projects/1/', {})
        request.user = self.other_user
        request.data = {}

        permission = IsClassProgrammer()
        view = Mock()
        view.action = 'partial_update'

        # other_user has no assignments
        has_permission = permission.has_object_permission(
            request, view, self.snow_project
        )
        self.assertFalse(has_permission)

    def test_multiple_users_can_have_same_class(self):
        """IO-756: Test that multiple users can be assigned to same class"""
        # Assign programmer_user to snow_class
        ClassProgrammerAssignment.objects.create(
            user=self.programmer_user,
            project_class=self.snow_class
        )

        # Assign other_user to snow_class (which programmer_user already has)
        ClassProgrammerAssignment.objects.create(
            user=self.other_user,
            project_class=self.snow_class
        )

        factory = APIRequestFactory()
        request = factory.patch('/projects/1/', {})
        request.data = {}
        permission = IsClassProgrammer()
        view = Mock()
        view.action = 'partial_update'

        # Check programmer_user still has access
        request.user = self.programmer_user
        self.assertTrue(permission.has_object_permission(request, view, self.snow_project))

        # Check other_user now has access
        request.user = self.other_user
        self.assertTrue(permission.has_object_permission(request, view, self.snow_project))

    def test_programmer_can_edit_assigned_class_project(self):
        factory = APIRequestFactory()
        request = factory.patch('/projects/1/', {})
        request.user = self.programmer_user
        request.data = {}

        permission = IsClassProgrammer()
        view = Mock()
        view.action = 'partial_update'

        has_permission = permission.has_object_permission(
            request, view, self.bridge_project
        )
        self.assertTrue(has_permission)

    def test_programmer_cannot_edit_unassigned_class_project(self):
        factory = APIRequestFactory()
        request = factory.patch('/projects/2/', {})
        request.user = self.programmer_user
        request.data = {}

        permission = IsClassProgrammer()
        view = Mock()
        view.action = 'partial_update'

        has_permission = permission.has_object_permission(
            request, view, self.snow_project
        )
        self.assertFalse(has_permission)

    def test_programmer_can_read_all_projects(self):
        factory = APIRequestFactory()
        request = factory.get('/projects/1/')
        request.user = self.programmer_user

        permission = IsClassProgrammer()
        view = Mock()
        view.action = 'retrieve'

        has_permission = permission.has_object_permission(
            request, view, self.snow_project
        )
        self.assertTrue(has_permission)

    def test_coordinator_bypasses_restrictions(self):
        factory = APIRequestFactory()
        request = factory.patch('/projects/1/', {})
        request.user = self.coordinator_user
        request.data = {}

        permission = IsClassProgrammer()
        view = Mock()
        view.action = 'partial_update'

        has_permission = permission.has_object_permission(
            request, view, self.snow_project
        )
        self.assertTrue(has_permission)

    def test_user_without_programmer_assignment_denied(self):
        factory = APIRequestFactory()
        request = factory.patch('/projects/1/', {})
        request.user = self.other_user
        request.data = {}

        permission = IsClassProgrammer()
        view = Mock()
        view.action = 'partial_update'

        has_permission = permission.has_object_permission(
            request, view, self.bridge_project
        )
        self.assertFalse(has_permission)

    def test_has_permission_allows_read_actions(self):
        factory = APIRequestFactory()
        request = factory.get('/projects/')
        request.user = self.programmer_user

        permission = IsClassProgrammer()
        view = Mock()
        view.action = 'list'

        has_permission = permission.has_permission(request, view)
        self.assertTrue(has_permission)

    def test_has_permission_allows_update_actions(self):
        factory = APIRequestFactory()
        request = factory.patch('/projects/1/', {})
        request.user = self.programmer_user

        permission = IsClassProgrammer()
        view = Mock()
        view.action = 'partial_update'

        has_permission = permission.has_permission(request, view)
        self.assertTrue(has_permission)

    def test_project_without_class_is_denied(self):
        phase = ProjectPhase.objects.first()
        project_no_class = Project.objects.create(
            name='Project Without Class',
            description='Test project without class',
            projectClass=None,
            phase=phase
        )

        factory = APIRequestFactory()
        request = factory.patch('/projects/no-class/', {})
        request.user = self.programmer_user
        request.data = {}

        permission = IsClassProgrammer()
        view = Mock()
        view.action = 'partial_update'

        has_permission = permission.has_object_permission(
            request, view, project_no_class
        )
        self.assertFalse(has_permission)

    def test_viewset_permission_integration(self):
        from infraohjelmointi_api.views.ProjectViewSet import ProjectViewSet

        self.assertTrue(issubclass(ProjectViewSet, BaseViewSet))

        permission_classes = BaseViewSet.permission_classes
        self.assertIsNotNone(permission_classes)

        permission = IsClassProgrammer()
        self.assertIsNotNone(permission)
        self.assertTrue(hasattr(permission, 'has_permission'))
        self.assertTrue(hasattr(permission, 'has_object_permission'))

    def test_permission_class_imports(self):
        from infraohjelmointi_api.permissions import (
            IsClassProgrammer, IsCoordinator, IsPlanner, IsProjectManager,
            IsPlannerOfProjectAreas, IsAdmin, IsViewer
        )

        self.assertTrue(IsClassProgrammer)
        self.assertTrue(IsCoordinator)
        self.assertTrue(IsPlanner)
        self.assertTrue(IsProjectManager)
        self.assertTrue(IsPlannerOfProjectAreas)
        self.assertTrue(IsAdmin)
        self.assertTrue(IsViewer)

    def test_cross_class_restrictions(self):
        # Create users and programmers
        user1 = User.objects.create_user(username='user1@test.fi', email='user1@test.fi')
        user2 = User.objects.create_user(username='user2@test.fi', email='user2@test.fi')

        for user in [user1, user2]:
            user.ad_groups.add(self.restricted_programmer_group)

        programmer1 = ProjectProgrammer.objects.create(firstName='User', lastName='One', person=None)
        programmer2 = ProjectProgrammer.objects.create(firstName='User', lastName='Two', person=None)

        # Create classes and assign
        bridge_class = ProjectClass.objects.create(
            name='B Siltojen peruskorjaus ja uusiminen - Cross Test',
            path='8 03 Kadut ja liikenneväylät/8 03 01 Uudisrakentaminen ja perusparantaminen sekä muut investoinnit, Kaupunkiympäristölautakunnan käytettäväksi/8 03 01 02 Perusparantaminen ja liikennejärjestelyt/B Siltojen peruskorjaus ja uusiminen - Cross Test'
        )
        snow_class = ProjectClass.objects.create(
            name='B Lumenvastaanottopaikat ja hiekkasiilot - Cross Test',
            path='8 03 Kadut ja liikenneväylät/8 03 01 Uudisrakentaminen ja perusparantaminen sekä muut investoinnit, Kaupunkiympäristölautakunnan käytettäväksi/8 03 01 03 Muut investoinnit/B Lumenvastaanottopaikat ja hiekkasiilot - Cross Test'
        )

        bridge_class.defaultProgrammer = programmer1
        bridge_class.save()
        snow_class.defaultProgrammer = programmer2
        snow_class.save()

        # Create test projects
        phase = ProjectPhase.objects.first()
        bridge_project = Project.objects.create(
            name='Bridge Project',
            description='Bridge project description',
            projectClass=bridge_class,
            phase=phase
        )
        snow_project = Project.objects.create(
            name='Snow Project',
            description='Snow project description',
            projectClass=snow_class,
            phase=phase
        )

        # Test cross-restrictions
        factory = APIRequestFactory()
        permission = IsClassProgrammer()
        view = Mock()
        view.action = 'partial_update'

        # User1 should NOT be able to edit snow projects
        request = factory.patch('/projects/1/', {})
        request.user = user1
        request.data = {}

        self.assertFalse(
            permission.has_object_permission(request, view, snow_project)
        )

        # User2 should NOT be able to edit bridge projects
        request.user = user2
        self.assertFalse(
            permission.has_object_permission(request, view, bridge_project)
        )

    def test_has_permission_allows_custom_get_actions(self):
        """IO-756: Test that custom project lists and search are allowed"""
        factory = APIRequestFactory()
        permission = IsClassProgrammer()
        view = Mock()
        
        # Test a few critical custom actions
        for action in ['get_projects_by_financial_year', 'get_search_results', 'get_coordinator_classes']:
            request = factory.get(f'/projects/{action}/')
            request.user = self.programmer_user
            view.action = action
            self.assertTrue(permission.has_permission(request, view), f"Action {action} should be allowed")

    def test_hierarchical_class_access(self):
        """IO-756: Test that assignment to parent class grants access to sub-classes"""
        # Create a sub-class of bridge_class
        sub_bridge_class = ProjectClass.objects.create(
            name='B Siltojen erikoiskorjaukset',
            parent=self.bridge_class,
            path=f"{self.bridge_class.path}/B Siltojen erikoiskorjaukset"
        )
        sub_bridge_project = Project.objects.create(
            name='Sub Bridge Project',
            description='Sub bridge project description',
            hkrId=12345,
            projectClass=sub_bridge_class,
            phase=self.bridge_project.phase
        )

        # Assign user to PARENT bridge_class
        ClassProgrammerAssignment.objects.create(
            user=self.programmer_user,
            project_class=self.bridge_class
        )

        factory = APIRequestFactory()
        request = factory.patch(f'/projects/{sub_bridge_project.id}/', {})
        request.user = self.programmer_user
        request.data = {}
        permission = IsClassProgrammer()
        view = Mock()
        view.action = 'partial_update'

        # Should have access because sub-class path starts with parent class path
        self.assertTrue(permission.has_object_permission(request, view, sub_bridge_project))

    def test_note_edit_permission(self):
        """IO-756: Test that restricted programmer can edit notes for their projects"""
        # Assign user to bridge_class
        ClassProgrammerAssignment.objects.create(
            user=self.programmer_user,
            project_class=self.bridge_class
        )
        
        test_note = Note.objects.create(
            content="Test note content",
            project=self.bridge_project,
            updatedBy=self.programmer_user
        )

        factory = APIRequestFactory()
        request = factory.patch(f'/notes/{test_note.id}/', {})
        request.user = self.programmer_user
        request.data = {}
        permission = IsClassProgrammer()
        view = Mock()
        view.action = 'partial_update'

        # Should be able to edit note because associated project is in an assigned class
        self.assertTrue(permission.has_object_permission(request, view, test_note))

    def test_project_group_edit_permission(self):
        """IO-756: Test that restricted programmer can edit project groups for their classes"""
        # Assign user to bridge_class
        ClassProgrammerAssignment.objects.create(
            user=self.programmer_user,
            project_class=self.bridge_class
        )
        
        test_group = ProjectGroup.objects.create(
            name="Test Group",
            classRelation=self.bridge_class
        )

        factory = APIRequestFactory()
        request = factory.patch(f'/project-groups/{test_group.id}/', {})
        request.user = self.programmer_user
        request.data = {}
        permission = IsClassProgrammer()
        view = Mock()
        view.action = 'partial_update'

        # Should be able to edit group because its classRelation is assigned to user
        self.assertTrue(permission.has_object_permission(request, view, test_group))

    # ------------------------------------------------------------------
    # IO-756 part 2: defensive restrictions for overlapping AD groups and
    # bulk project updates.
    # ------------------------------------------------------------------

    def _make_user_with_groups(self, email, group_names):
        user = User.objects.create_user(username=email, email=email)
        for name in group_names:
            group, _ = ADGroup.objects.get_or_create(name=name)
            user.ad_groups.add(group)
        return user

    def test_is_planner_denies_when_user_also_in_restricted_group(self):
        """Restricted programmers in the ohjelmoijat group must not get planner access."""
        user = self._make_user_with_groups(
            'overlap.planner@test.fi',
            ['sg_kymp_sso_io_ohjelmoijat', self.restricted_programmer_group.name],
        )

        factory = APIRequestFactory()
        request = factory.patch('/projects/1/', {})
        request.user = user
        request.data = {}
        view = Mock()
        view.action = 'partial_update'
        view.kwargs = {}

        permission = IsPlanner()
        self.assertFalse(permission.has_permission(request, view))
        self.assertFalse(
            permission.has_object_permission(request, view, self.snow_project)
        )

    def test_is_project_manager_denies_when_user_also_in_restricted_group(self):
        user = self._make_user_with_groups(
            'overlap.pm@test.fi',
            ['sg_kymp_sso_io_projektipaallikot', self.restricted_programmer_group.name],
        )

        factory = APIRequestFactory()
        request = factory.patch('/projects/1/', {})
        request.user = user
        request.data = {}
        view = Mock()
        view.action = 'partial_update'

        permission = IsProjectManager()
        self.assertFalse(permission.has_permission(request, view))
        self.assertFalse(
            permission.has_object_permission(request, view, self.snow_project)
        )

    def test_is_planner_of_project_areas_denies_when_user_also_in_restricted_group(self):
        user = self._make_user_with_groups(
            'overlap.area@test.fi',
            [
                'sg_kymp_sso_io_projektialueiden_ohjelmoijat',
                self.restricted_programmer_group.name,
            ],
        )

        factory = APIRequestFactory()
        request = factory.patch('/projects/1/', {})
        request.user = user
        request.data = {}
        view = Mock()
        view.action = 'partial_update'

        permission = IsPlannerOfProjectAreas()
        self.assertFalse(permission.has_permission(request, view))
        self.assertFalse(
            permission.has_object_permission(request, view, self.snow_project)
        )

    def test_is_planner_still_grants_access_without_restricted_group(self):
        """Regression: plain planners keep working after the defensive check."""
        user = self._make_user_with_groups(
            'plain.planner@test.fi',
            ['sg_kymp_sso_io_ohjelmoijat'],
        )

        factory = APIRequestFactory()
        request = factory.get('/projects/')
        request.user = user
        view = Mock()
        view.action = 'list'
        view.kwargs = {}

        permission = IsPlanner()
        self.assertTrue(permission.has_permission(request, view))
        self.assertTrue(
            permission.has_object_permission(request, view, self.snow_project)
        )

    def test_is_class_programmer_allows_patch_bulk_projects_action(self):
        """IO-756 part 2: bulk-update action must be allowed at view level."""
        factory = APIRequestFactory()
        request = factory.patch('/projects/bulk-update/', {})
        request.user = self.programmer_user
        request.data = {}

        permission = IsClassProgrammer()
        view = Mock()
        view.action = 'patch_bulk_projects'

        self.assertTrue(permission.has_permission(request, view))

    def test_bulk_update_helper_allows_projects_in_assigned_classes(self):
        """IO-756 part 2: restricted programmer may bulk-update within assigned class."""
        from infraohjelmointi_api.views.ProjectViewSet import ProjectViewSet

        ClassProgrammerAssignment.objects.create(
            user=self.programmer_user, project_class=self.bridge_class
        )

        factory = APIRequestFactory()
        request = factory.patch('/projects/bulk-update/', {})
        request.user = self.programmer_user

        viewset = ProjectViewSet()
        response = viewset._enforce_restricted_bulk_update_access(
            request, [str(self.bridge_project.id)]
        )
        self.assertIsNone(response)

    def test_bulk_update_helper_blocks_project_outside_assigned_classes(self):
        """IO-756 part 2: restricted programmer can't bulk-update foreign projects."""
        from infraohjelmointi_api.views.ProjectViewSet import ProjectViewSet

        ClassProgrammerAssignment.objects.create(
            user=self.programmer_user, project_class=self.bridge_class
        )

        factory = APIRequestFactory()
        request = factory.patch('/projects/bulk-update/', {})
        request.user = self.programmer_user

        viewset = ProjectViewSet()
        response = viewset._enforce_restricted_bulk_update_access(
            request,
            [str(self.bridge_project.id), str(self.snow_project.id)],
        )
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)
        self.assertIn(
            str(self.snow_project.id),
            response.data.get("unauthorized_project_ids", []),
        )
        self.assertNotIn(
            str(self.bridge_project.id),
            response.data.get("unauthorized_project_ids", []),
        )

    def test_bulk_update_helper_noop_for_non_restricted_user(self):
        """Non-restricted users bypass the bulk-update access check entirely."""
        from infraohjelmointi_api.views.ProjectViewSet import ProjectViewSet

        factory = APIRequestFactory()
        request = factory.patch('/projects/bulk-update/', {})
        request.user = self.coordinator_user

        viewset = ProjectViewSet()
        response = viewset._enforce_restricted_bulk_update_access(
            request,
            [str(self.bridge_project.id), str(self.snow_project.id)],
        )
        self.assertIsNone(response)

    def test_bulk_update_helper_denies_when_no_assignments(self):
        """Restricted programmer with no assigned classes is denied outright."""
        from infraohjelmointi_api.views.ProjectViewSet import ProjectViewSet

        factory = APIRequestFactory()
        request = factory.patch('/projects/bulk-update/', {})
        request.user = self.other_user  # restricted group, no assignments

        viewset = ProjectViewSet()
        response = viewset._enforce_restricted_bulk_update_access(
            request, [str(self.bridge_project.id)]
        )
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)
