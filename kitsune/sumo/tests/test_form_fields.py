from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile

from kitsune.sumo.form_fields import ImagePlusField, TypedMultipleChoiceField
from kitsune.sumo.tests import TestCase


class TypedMultipleChoiceFieldTestCase(TestCase):
    """TypedMultipleChoiceField is just like MultipleChoiceField
    except, instead of validating, it coerces types."""

    def assertRaisesErrorWithMessage(self, error, message, callable, *args, **kwargs):
        self.assertRaises(error, callable, *args, **kwargs)
        try:
            callable(*args, **kwargs)
        except error as e:
            self.assertEqual(message, str(e))

    def test_typedmultiplechoicefield_71(self):
        f = TypedMultipleChoiceField(choices=[(1, "+1"), (-1, "-1")], coerce=int)
        self.assertEqual([1], f.clean(["1"]))
        self.assertRaisesErrorWithMessage(
            ValidationError,
            "['Select a valid choice. 2 is not one of the available choices." "']",
            f.clean,
            ["2"],
        )

    def test_typedmultiplechoicefield_72(self):
        # Different coercion, same validation.
        f = TypedMultipleChoiceField(choices=[(1, "+1"), (-1, "-1")], coerce=float)
        self.assertEqual([1.0], f.clean(["1"]))

    def test_typedmultiplechoicefield_73(self):
        # This can also cause weirdness: bool(-1) == True
        f = TypedMultipleChoiceField(choices=[(1, "+1"), (-1, "-1")], coerce=bool)
        self.assertEqual([True], f.clean(["-1"]))

    def test_typedmultiplechoicefield_74(self):
        # Even more weirdness: if you have a valid choice but your coercion
        # function can't coerce, you'll still get a validation error.
        # Don't do this!
        f = TypedMultipleChoiceField(choices=[("A", "A"), ("B", "B")], coerce=int)
        self.assertRaisesErrorWithMessage(
            ValidationError,
            "['Select a valid choice. B is not one of the available choices." "']",
            f.clean,
            ["B"],
        )
        # Required fields require values
        self.assertRaisesErrorWithMessage(
            ValidationError, "['This field is required.']", f.clean, []
        )

    def test_typedmultiplechoicefield_75(self):
        # Non-required fields aren't required
        f = TypedMultipleChoiceField(choices=[(1, "+1"), (-1, "-1")], coerce=int, required=False)
        self.assertEqual([], f.clean([]))

    def test_typedmultiplechoicefield_76(self):
        # If you want cleaning an empty value to return a different type,
        # tell the field
        f = TypedMultipleChoiceField(
            choices=[(1, "+1"), (-1, "-1")], coerce=int, required=False, empty_value=None
        )
        self.assertEqual(None, f.clean([]))

    def test_coerce_only(self):
        """No validation error raised in this case."""
        f = TypedMultipleChoiceField(choices=[(1, "+1")], coerce=int, coerce_only=True)
        self.assertEqual([], f.clean(["2"]))


class ImagePlusFieldTestCases(TestCase):
    """
    Test cases for kitsune.sumo.form_fields.ImagePlusField, which accepts SVG images
    as well as the images accepted by django.forms.ImageField.
    """

    def get_uploaded_file(self, name, kind="simple", content=None):
        if content is None:
            content = b"""
                <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
                    <rect x="10" y="10" width="80" height="80" fill="blue" />
                </svg>
            """
        content_type = "image/svg+xml"

        if kind == "simple":
            return SimpleUploadedFile(name, content, content_type)

        data = TemporaryUploadedFile(name, content_type, len(content), None)
        data.open("wb").write(content)
        return data

    def test_svg_image_with_temp_file(self):
        """Test for the case when the uploaded file is a named temporary file instance."""
        field = ImagePlusField()
        data = self.get_uploaded_file("stuff.svg", "temp")
        self.assertEqual(field.clean(data), data)

    def test_svg_image_with_in_memory_file(self):
        """Test for the case when the uploaded file is an in-memory file instance."""
        field = ImagePlusField()
        data = self.get_uploaded_file("stuff.svg")
        self.assertEqual(field.clean(data), data)

    def test_svg_image_without_proper_extension(self):
        """SVG images without an "svg" extension should be considered invalid."""
        field = ImagePlusField()
        data = self.get_uploaded_file("stuff")

        with self.assertRaises(ValidationError) as arm:
            field.clean(data)

        self.assertTrue(hasattr(arm.exception, "code"))
        self.assertEqual(arm.exception.code, "invalid_image")
