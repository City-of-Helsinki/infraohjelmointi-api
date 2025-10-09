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
            ("8 01 02 Test, Kaupunkiympäristölautakunnan käytettäväksi", "8 01 02 Test"),
            ("8 01 03 Test, KHN käytettäväksi", "8 01 03 Test"),
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
            "8 01 99 Test, Kaupunkiympäristölautakunnan käytettäväksi"
        )
