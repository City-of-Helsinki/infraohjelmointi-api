"""
Tests for ProjectClassSerializer to ensure defaultProgrammer field serialization works correctly.
This addresses the IO-411 frontend integration requirements.
"""

from django.test import TestCase
from rest_framework.renderers import JSONRenderer
from infraohjelmointi_api.models import ProjectClass, ProjectProgrammer, Person
from infraohjelmointi_api.serializers import ProjectClassSerializer
import uuid


class ProjectClassSerializerTestCase(TestCase):
    """Test ProjectClassSerializer includes defaultProgrammer field properly"""

    project_class_id = uuid.UUID("7c5b981e-286f-4065-9d9e-29d8d1714e4c")
    programmer_id = uuid.UUID("33814e76-7bdc-47c2-bf08-7ed43a96e042")
    person_id = uuid.UUID("fdc89f56-b631-4109-a137-45b950de6b10")

    @classmethod
    def setUpTestData(cls):
        # Create test person
        cls.person = Person.objects.create(
            id=cls.person_id,
            firstName="John",
            lastName="Doe",
            email="john.doe@example.com",
            title="Developer",
            phone="1234567890"
        )

        # Create test programmer
        cls.programmer = ProjectProgrammer.objects.create(
            id=cls.programmer_id,
            firstName="Alice",
            lastName="Smith",
            person=cls.person
        )

        # Create test project class with default programmer
        cls.project_class = ProjectClass.objects.create(
            id=cls.project_class_id,
            name="Test Suurpiiri Class",
            path="test/path",
            forCoordinatorOnly=False,
            defaultProgrammer=cls.programmer
        )

        # Create project class without default programmer for comparison
        cls.project_class_no_programmer = ProjectClass.objects.create(
            id=uuid.uuid4(),
            name="Test Class No Programmer",
            path="test/no-programmer",
            forCoordinatorOnly=False
        )

    def test_project_class_serializer_includes_default_programmer(self):
        """Test that ProjectClassSerializer includes full defaultProgrammer object"""
        serializer = ProjectClassSerializer(self.project_class)
        data = serializer.data

        # Check that defaultProgrammer field exists
        self.assertIn('defaultProgrammer', data)

        # Check that it's not None
        self.assertIsNotNone(data['defaultProgrammer'])

        # Check that it's a dict (object) not just an ID
        self.assertIsInstance(data['defaultProgrammer'], dict)

        # Verify the structure of the defaultProgrammer object
        programmer_data = data['defaultProgrammer']
        self.assertEqual(programmer_data['id'], str(self.programmer_id))
        self.assertEqual(programmer_data['firstName'], 'Alice')
        self.assertEqual(programmer_data['lastName'], 'Smith')

        # Should also include person if linked
        self.assertIn('person', programmer_data)

    def test_project_class_serializer_no_default_programmer(self):
        """Test that ProjectClassSerializer handles null defaultProgrammer correctly"""
        serializer = ProjectClassSerializer(self.project_class_no_programmer)
        data = serializer.data

        # Check that defaultProgrammer field exists but is None
        self.assertIn('defaultProgrammer', data)
        self.assertIsNone(data['defaultProgrammer'])

    def test_project_class_serializer_response_structure(self):
        """Test that the serializer includes all expected fields"""
        serializer = ProjectClassSerializer(self.project_class)
        data = serializer.data

        # Check that all expected fields are present
        expected_fields = ['id', 'name', 'path', 'forCoordinatorOnly', 'defaultProgrammer']
        for field in expected_fields:
            self.assertIn(field, data, f"Field {field} should be included in serializer")

    def test_suurpiiri_programmer_assignment_serialization(self):
        """Test serialization of suurpiiri classes with programmer assignments"""
        # Create a suurpiiri class similar to production data
        suurpiiri_class = ProjectClass.objects.create(
            id=uuid.uuid4(),
            name="Kaakkoinen suurpiiri",
            path="8/Kaakkoinen suurpiiri",
            forCoordinatorOnly=False,
            defaultProgrammer=self.programmer
        )

        serializer = ProjectClassSerializer(suurpiiri_class)
        data = serializer.data

        # Verify suurpiiri-specific serialization
        self.assertEqual(data['name'], 'Kaakkoinen suurpiiri')
        self.assertIsNotNone(data['defaultProgrammer'])
        self.assertEqual(data['defaultProgrammer']['firstName'], 'Alice')
        self.assertEqual(data['defaultProgrammer']['lastName'], 'Smith')

    def test_multiple_project_classes_serialization(self):
        """Test serialization of multiple project classes (like in API list response)"""
        queryset = ProjectClass.objects.filter(
            id__in=[self.project_class.id, self.project_class_no_programmer.id]
        )

        serializer = ProjectClassSerializer(queryset, many=True)
        data = serializer.data

        self.assertEqual(len(data), 2)

        # Find the class with programmer
        class_with_programmer = next(
            (item for item in data if item['name'] == 'Test Suurpiiri Class'),
            None
        )
        self.assertIsNotNone(class_with_programmer)
        self.assertIsNotNone(class_with_programmer['defaultProgrammer'])

        # Find the class without programmer
        class_without_programmer = next(
            (item for item in data if item['name'] == 'Test Class No Programmer'),
            None
        )
        self.assertIsNotNone(class_without_programmer)
        self.assertIsNone(class_without_programmer['defaultProgrammer'])

    def test_json_rendering_compatibility(self):
        """Test that the serialized data can be properly JSON rendered"""
        serializer = ProjectClassSerializer(self.project_class)
        data = serializer.data

        # This should not raise any exceptions
        json_output = JSONRenderer().render(data)

        # Verify JSON contains the programmer data
        self.assertIn(b'"defaultProgrammer"', json_output)
        self.assertIn(b'"firstName"', json_output)
        self.assertIn(b'"lastName"', json_output)
        self.assertIn(b'Alice', json_output)
        self.assertIn(b'Smith', json_output)

    def test_programmer_person_relationship_serialization(self):
        """Test that programmer's person relationship is properly serialized"""
        serializer = ProjectClassSerializer(self.project_class)
        data = serializer.data

        programmer_data = data['defaultProgrammer']

        # Should include person field
        self.assertIn('person', programmer_data)

        # Person field should contain the person ID (since person is linked)
        # The serializer returns UUID objects, so we need to convert to string for comparison
        if programmer_data['person']:
            self.assertEqual(str(programmer_data['person']), str(self.person_id))
        else:
            self.assertEqual(programmer_data['person'], str(self.person_id))

    def test_empty_programmer_serialization(self):
        """Test serialization when defaultProgrammer is the 'Ei Valintaa' empty programmer"""
        # Create empty programmer
        empty_programmer = ProjectProgrammer.objects.create(
            firstName="Ei",
            lastName="Valintaa",
            person=None
        )

        # Create class with empty programmer
        class_with_empty = ProjectClass.objects.create(
            name="Class with Empty Programmer",
            path="test/empty",
            forCoordinatorOnly=False,
            defaultProgrammer=empty_programmer
        )

        serializer = ProjectClassSerializer(class_with_empty)
        data = serializer.data

        # Should still serialize the empty programmer
        self.assertIsNotNone(data['defaultProgrammer'])
        self.assertEqual(data['defaultProgrammer']['firstName'], 'Ei')
        self.assertEqual(data['defaultProgrammer']['lastName'], 'Valintaa')
        self.assertIsNone(data['defaultProgrammer']['person'])

    def test_serializer_context_compatibility(self):
        """Test that serializer works with different context configurations"""
        # Test with empty context
        serializer = ProjectClassSerializer(self.project_class, context={})
        data = serializer.data
        self.assertIn('defaultProgrammer', data)

        # Test with request context (simulating API call)
        mock_request = type('MockRequest', (), {'user': None})()
        serializer = ProjectClassSerializer(
            self.project_class,
            context={'request': mock_request}
        )
        data = serializer.data
        self.assertIn('defaultProgrammer', data)

    def test_specific_programmer_assignments(self):
        """Test serialization of specific IO-411 programmer assignments"""
        # Create programmers from IO-411 assignments
        programmer_1 = ProjectProgrammer.objects.create(
            firstName="John",
            lastName="Doe"
        )

        programmer_2 = ProjectProgrammer.objects.create(
            firstName="Jane",
            lastName="Doe"
        )

        # Create classes with IO-411 assignments
        esirakentaminen = ProjectClass.objects.create(
            name="8 01 03 Esirakentaminen, täyttötyöt, rakentamiskelpoiseksi saattaminen, Kaupunkiympäristölautakunnan käytettäväksi",
            path="8/8 01/8 01 03",
            forCoordinatorOnly=True,
            defaultProgrammer=programmer_1
        )

        liikuntapaikat = ProjectClass.objects.create(
            name="8 02 Liikuntapaikat",
            path="8/8 02",
            forCoordinatorOnly=True,
            defaultProgrammer=programmer_2
        )

        # Test serialization
        esirakentaminen_serializer = ProjectClassSerializer(esirakentaminen)
        esirakentaminen_data = esirakentaminen_serializer.data

        self.assertEqual(
            esirakentaminen_data['defaultProgrammer']['firstName'],
            'John'
        )
        self.assertEqual(
            esirakentaminen_data['defaultProgrammer']['lastName'],
            'Doe'
        )

        liikuntapaikat_serializer = ProjectClassSerializer(liikuntapaikat)
        liikuntapaikat_data = liikuntapaikat_serializer.data

        self.assertEqual(
            liikuntapaikat_data['defaultProgrammer']['firstName'],
            'Jane'
        )
        self.assertEqual(
            liikuntapaikat_data['defaultProgrammer']['lastName'],
            'Doe'
        )

    def test_suffix_removal(self):
        """Test IO-758: Suffix removal for all variations"""
        test_cases = [
            ("8 01 01 Test, Kylkn käytettäväksi", "8 01 01 Test"),
            ("8 01 02 Test, kylkn käytettäväksi", "8 01 02 Test"),
            ("8 01 03 Test, Kaupunkiympäristölautakunnan käytettäväksi", "8 01 03 Test"),
            ("8 01 04 Test, kaupunkiympäristölautakunnan käytettäväksi", "8 01 04 Test"),
            ("8 01 05 Test, KHN käytettäväksi", "8 01 05 Test"),
            ("8 01 06 Test, Khn käytettäväksi", "8 01 06 Test"),
            ("8 01 07 Test, khn käytettäväksi", "8 01 07 Test"),
            ("8 01 08 Test, Kaupunginhallituksen käytettäväksi", "8 01 08 Test"),
            ("8 01 09 Test, kaupunginhallituksen käytettäväksi", "8 01 09 Test"),
        ]

        for original_name, expected_name in test_cases:
            with self.subTest(original_name=original_name):
                test_class = ProjectClass.objects.create(
                    name=original_name,
                    path="8/Test",
                    forCoordinatorOnly=True
                )

                serializer = ProjectClassSerializer(test_class)
                self.assertEqual(serializer.data['name'], expected_name)
                test_class.refresh_from_db()
                self.assertEqual(test_class.name, original_name)

    def test_numbering_addition(self):
        """Test IO-455: Numbering addition to programming classes"""
        coord_class = ProjectClass.objects.create(
            name="8 01 01 Kiinteistöjen ostot ja lunastukset, Kylkn käytettäväksi",
            path="8/8 01/8 01 01",
            forCoordinatorOnly=True
        )

        prog_class = ProjectClass.objects.create(
            name="Kiinteistöjen ostot ja lunastukset",
            path="8/Kiinteistöjen ostot ja lunastukset",
            forCoordinatorOnly=False
        )

        coord_class.relatedTo = prog_class
        coord_class.save()

        serializer = ProjectClassSerializer(prog_class)
        self.assertEqual(
            serializer.data['name'],
            "8 01 01 Kiinteistöjen ostot ja lunastukset"
        )

        prog_class.refresh_from_db()
        self.assertEqual(
            prog_class.name,
            "Kiinteistöjen ostot ja lunastukset"
        )

    def test_four_digit_numbering_addition(self):
        """Test IO-455: 4-digit numbering addition (8 03 01 01, 8 03 01 02, etc.)"""
        coord_class_1 = ProjectClass.objects.create(
            name="8 03 01 01 Uudisrakentaminen, Kylkn käytettäväksi",
            path="8/8 03/8 03 01/8 03 01 01",
            forCoordinatorOnly=True
        )

        prog_class_1 = ProjectClass.objects.create(
            name="Uudisrakentaminen",
            path="8/Uudisrakentaminen",
            forCoordinatorOnly=False
        )

        coord_class_1.relatedTo = prog_class_1
        coord_class_1.save()

        serializer = ProjectClassSerializer(prog_class_1)
        self.assertEqual(
            serializer.data['name'],
            "8 03 01 01 Uudisrakentaminen"
        )

        coord_class_2 = ProjectClass.objects.create(
            name="8 03 01 02 Perusparantaminen ja liikennejärjestelyt, Kylkn käytettäväksi",
            path="8/8 03/8 03 01/8 03 01 02",
            forCoordinatorOnly=True
        )

        prog_class_2 = ProjectClass.objects.create(
            name="Perusparantaminen ja liikennejärjestelyt",
            path="8/Perusparantaminen ja liikennejärjestelyt",
            forCoordinatorOnly=False
        )

        coord_class_2.relatedTo = prog_class_2
        coord_class_2.save()

        serializer = ProjectClassSerializer(prog_class_2)
        self.assertEqual(
            serializer.data['name'],
            "8 03 01 02 Perusparantaminen ja liikennejärjestelyt"
        )

    def test_programming_class_with_existing_numbering(self):
        """Test IO-455: Programming classes with existing numbering get replaced"""
        prog_with_numbering = ProjectClass.objects.create(
            name="8 99 99 Test Class With Existing Numbering",
            path="8/8 99 99 Test Class With Existing Numbering",
            forCoordinatorOnly=False
        )

        coord_class = ProjectClass.objects.create(
            name="8 01 01 Test Coordinator",
            path="8/8 01/8 01 01",
            forCoordinatorOnly=True
        )

        coord_class.relatedTo = prog_with_numbering
        coord_class.save()

        serializer = ProjectClassSerializer(prog_with_numbering)
        self.assertEqual(
            serializer.data['name'],
            "8 01 01 Test Class With Existing Numbering"
        )

    def test_edge_cases(self):
        """Test edge cases: no relationship, no numbering, multiple suffixes"""
        orphan_prog_class = ProjectClass.objects.create(
            name="Orphan Programming Class",
            path="8/Orphan Programming Class",
            forCoordinatorOnly=False
        )

        serializer = ProjectClassSerializer(orphan_prog_class)
        self.assertEqual(serializer.data['name'], "Orphan Programming Class")

        coord_no_numbering = ProjectClass.objects.create(
            name="Coordinator Without Numbering",
            path="8/Coordinator Without Numbering",
            forCoordinatorOnly=True
        )

        prog_class = ProjectClass.objects.create(
            name="Programming for No Numbering",
            path="8/Programming for No Numbering",
            forCoordinatorOnly=False
        )

        coord_no_numbering.relatedTo = prog_class
        coord_no_numbering.save()

        serializer = ProjectClassSerializer(prog_class)
        self.assertEqual(serializer.data['name'], "Programming for No Numbering")

        multi_suffix_class = ProjectClass.objects.create(
            name="8 01 99 Test, Kylkn käytettäväksi, Kaupunkiympäristölautakunnan käytettäväksi",
            path="8/8 01/8 01 99",
            forCoordinatorOnly=True
        )

        serializer = ProjectClassSerializer(multi_suffix_class)
        self.assertEqual(
            serializer.data['name'],
            "8 01 99 Test"
        )


class ComputedDefaultProgrammerTestCase(TestCase):
    """Test computedDefaultProgrammer field with hierarchical fallback logic"""

    @classmethod
    def setUpTestData(cls):
        # Create test programmers
        cls.programmer_1 = ProjectProgrammer.objects.create(
            firstName="Alice",
            lastName="Smith"
        )

        cls.programmer_2 = ProjectProgrammer.objects.create(
            firstName="Bob",
            lastName="Johnson"
        )

        cls.programmer_3 = ProjectProgrammer.objects.create(
            firstName="Charlie",
            lastName="Brown"
        )

        # Create hierarchical class structure
        # Root level
        cls.root_class = ProjectClass.objects.create(
            name="8 03 Kadut ja liikenneväylät",
            path="8 03 Kadut ja liikenneväylät",
            forCoordinatorOnly=False
        )

        # Level 1 - has default programmer
        cls.level1_class = ProjectClass.objects.create(
            name="8 03 01 Uudisrakentaminen ja perusparantaminen",
            path="8 03 Kadut ja liikenneväylät/8 03 01 Uudisrakentaminen ja perusparantaminen",
            parent=cls.root_class,
            forCoordinatorOnly=False,
            defaultProgrammer=cls.programmer_1
        )

        # Level 2 - no default programmer
        cls.level2_class = ProjectClass.objects.create(
            name="8 03 01 02 Perusparantaminen ja liikennejärjestelyt",
            path="8 03 Kadut ja liikenneväylät/8 03 01 Uudisrakentaminen ja perusparantaminen/8 03 01 02 Perusparantaminen ja liikennejärjestelyt",
            parent=cls.level1_class,
            forCoordinatorOnly=False
        )

        # Level 3 - no default programmer (Saija's case)
        cls.level3_class = ProjectClass.objects.create(
            name="E Liikennejärjestelyt",
            path="8 03 Kadut ja liikenneväylät/8 03 01 Uudisrakentaminen ja perusparantaminen/8 03 01 02 Perusparantaminen ja liikennejärjestelyt/E Liikennejärjestelyt",
            parent=cls.level2_class,
            forCoordinatorOnly=False
        )

        # Another branch with different programmer
        cls.other_level1_class = ProjectClass.objects.create(
            name="8 03 02 Projektialueiden kadut",
            path="8 03 Kadut ja liikenneväylät/8 03 02 Projektialueiden kadut",
            parent=cls.root_class,
            forCoordinatorOnly=False,
            defaultProgrammer=cls.programmer_2
        )

        # Class with no parent hierarchy and no default programmer
        cls.orphan_class = ProjectClass.objects.create(
            name="Orphan Class",
            path="Orphan Class",
            forCoordinatorOnly=False
        )

        # Class with direct default programmer
        cls.direct_class = ProjectClass.objects.create(
            name="Direct Class",
            path="Direct Class",
            forCoordinatorOnly=False,
            defaultProgrammer=cls.programmer_3
        )

    def test_computed_default_programmer_direct_assignment(self):
        """Test that class with direct default programmer returns it"""
        serializer = ProjectClassSerializer(self.direct_class)
        data = serializer.data

        self.assertIn('computedDefaultProgrammer', data)
        self.assertIsNotNone(data['computedDefaultProgrammer'])
        self.assertEqual(data['computedDefaultProgrammer']['firstName'], 'Charlie')
        self.assertEqual(data['computedDefaultProgrammer']['lastName'], 'Brown')

    def test_computed_default_programmer_hierarchical_fallback(self):
        """Test that class without default programmer inherits from parent"""
        serializer = ProjectClassSerializer(self.level3_class)
        data = serializer.data

        self.assertIn('computedDefaultProgrammer', data)
        self.assertIsNotNone(data['computedDefaultProgrammer'])
        # Should inherit from level1_class (Alice Smith)
        self.assertEqual(data['computedDefaultProgrammer']['firstName'], 'Alice')
        self.assertEqual(data['computedDefaultProgrammer']['lastName'], 'Smith')

    def test_computed_default_programmer_multi_level_fallback(self):
        """Test that class inherits from grandparent when parent has no default"""
        serializer = ProjectClassSerializer(self.level2_class)
        data = serializer.data

        self.assertIn('computedDefaultProgrammer', data)
        self.assertIsNotNone(data['computedDefaultProgrammer'])
        # Should inherit from level1_class (Alice Smith)
        self.assertEqual(data['computedDefaultProgrammer']['firstName'], 'Alice')
        self.assertEqual(data['computedDefaultProgrammer']['lastName'], 'Smith')

    def test_computed_default_programmer_no_fallback(self):
        """Test that class with no hierarchy and no default returns None"""
        serializer = ProjectClassSerializer(self.orphan_class)
        data = serializer.data

        self.assertIn('computedDefaultProgrammer', data)
        self.assertIsNone(data['computedDefaultProgrammer'])

    def test_computed_default_programmer_different_branches(self):
        """Test that different branches return their respective programmers"""
        # Test level3_class (should get Alice from level1)
        serializer1 = ProjectClassSerializer(self.level3_class)
        data1 = serializer1.data
        self.assertEqual(data1['computedDefaultProgrammer']['firstName'], 'Alice')

        # Test other_level1_class (should get Bob directly)
        serializer2 = ProjectClassSerializer(self.other_level1_class)
        data2 = serializer2.data
        self.assertEqual(data2['computedDefaultProgrammer']['firstName'], 'Bob')

    def test_computed_vs_default_programmer_consistency(self):
        """Test that computedDefaultProgrammer matches defaultProgrammer when both exist"""
        serializer = ProjectClassSerializer(self.level1_class)
        data = serializer.data

        # Both should return the same programmer
        self.assertEqual(
            data['defaultProgrammer']['id'],
            data['computedDefaultProgrammer']['id']
        )
        self.assertEqual(
            data['defaultProgrammer']['firstName'],
            data['computedDefaultProgrammer']['firstName']
        )

    def test_computed_default_programmer_serialization_structure(self):
        """Test that computedDefaultProgrammer has proper serialization structure"""
        serializer = ProjectClassSerializer(self.level3_class)
        data = serializer.data

        computed = data['computedDefaultProgrammer']
        self.assertIsInstance(computed, dict)
        self.assertIn('id', computed)
        self.assertIn('firstName', computed)
        self.assertIn('lastName', computed)
        self.assertIn('person', computed)

    def test_saija_case_simulation(self):
        """Test the specific case mentioned in Jira: Saija's traffic arrangements"""
        # This simulates the exact scenario from the Jira ticket
        # "Katujen perusparantamiseen liikennejärjestelyjen alle itäiseen suurpiiriin"

        # Create the specific hierarchy mentioned
        itainen_suurpiiri = ProjectClass.objects.create(
            name="Itäinen suurpiiri",
            path="8 03 Kadut ja liikenneväylät/Uudisrakentaminen/Itäinen suurpiiri",
            parent=self.root_class,
            forCoordinatorOnly=False,
            defaultProgrammer=self.programmer_1  # Saija Vihervaara
        )

        # Test that the traffic class inherits from suurpiiri
        serializer = ProjectClassSerializer(self.level3_class)
        data = serializer.data

        # Should get the programmer from the hierarchy (Alice Smith in our test)
        self.assertIsNotNone(data['computedDefaultProgrammer'])
        self.assertEqual(data['computedDefaultProgrammer']['firstName'], 'Alice')

    def test_deep_hierarchy_fallback(self):
        """Test fallback through multiple levels of hierarchy"""
        # Create a deeper hierarchy
        level4_class = ProjectClass.objects.create(
            name="Level 4 Class",
            path="8 03/Level 1/Level 2/Level 3/Level 4",
            parent=self.level3_class,
            forCoordinatorOnly=False
        )

        serializer = ProjectClassSerializer(level4_class)
        data = serializer.data

        # Should inherit from level1_class (Alice Smith) through the hierarchy
        self.assertIsNotNone(data['computedDefaultProgrammer'])
        self.assertEqual(data['computedDefaultProgrammer']['firstName'], 'Alice')

    def test_computed_default_programmer_with_none_parents(self):
        """Test behavior when some parents in hierarchy are None"""
        # Create a class with None parent
        class_with_none_parent = ProjectClass.objects.create(
            name="Class with None Parent",
            path="Class with None Parent",
            parent=None,
            forCoordinatorOnly=False
        )

        serializer = ProjectClassSerializer(class_with_none_parent)
        data = serializer.data

        # Should return None since no hierarchy and no default
        self.assertIsNone(data['computedDefaultProgrammer'])

    def test_computed_default_programmer_json_serialization(self):
        """Test that computedDefaultProgrammer can be JSON serialized"""
        serializer = ProjectClassSerializer(self.level3_class)
        data = serializer.data

        # This should not raise any exceptions
        json_output = JSONRenderer().render(data)

        # Verify JSON contains the computed programmer data
        self.assertIn(b'"computedDefaultProgrammer"', json_output)
        self.assertIn(b'"Alice"', json_output)
        self.assertIn(b'"Smith"', json_output)

    def test_computed_default_programmer_multiple_classes(self):
        """Test computedDefaultProgrammer with multiple classes (list serialization)"""
        classes = [self.level3_class, self.direct_class, self.orphan_class]
        serializer = ProjectClassSerializer(classes, many=True)
        data = serializer.data

        self.assertEqual(len(data), 3)

        # Find each class in the results
        level3_data = next(item for item in data if item['name'] == 'E Liikennejärjestelyt')
        direct_data = next(item for item in data if item['name'] == 'Direct Class')
        orphan_data = next(item for item in data if item['name'] == 'Orphan Class')

        # Verify computedDefaultProgrammer for each
        self.assertIsNotNone(level3_data['computedDefaultProgrammer'])
        self.assertEqual(level3_data['computedDefaultProgrammer']['firstName'], 'Alice')

        self.assertIsNotNone(direct_data['computedDefaultProgrammer'])
        self.assertEqual(direct_data['computedDefaultProgrammer']['firstName'], 'Charlie')

        self.assertIsNone(orphan_data['computedDefaultProgrammer'])
