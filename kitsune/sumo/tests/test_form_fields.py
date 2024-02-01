from django.core.exceptions import ValidationError

from kitsune.sumo.form_fields import TypedMultipleChoiceField
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
