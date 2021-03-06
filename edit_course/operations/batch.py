import json
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from exercise.models import BaseExercise, Submission
from lib.helpers import extract_form_errors
from ..submission_forms import BatchSubmissionCreateAndReviewForm


def create_submissions(instance, admin_profile, json_text):
    """
    Batch creates submissions and feedback from formatted JSON.
    """
    try:
        submissions_json = json.loads(json_text)
    except Exception as e:
        return [_("Failed to parse the JSON: {}").format(str(e))]
    if not "objects" in submissions_json:
        return [_('Missing JSON field: objects')]

    errors = []
    validated_forms = []
    count = 0
    for submission_json in submissions_json["objects"]:
        count += 1
        if not "exercise_id" in submission_json:
            errors.append(
                _('Missing field "exercise_id" in object {count:d}.')\
                    .format(count=count))
            continue

        exercise = BaseExercise.objects.filter(
            id=submission_json["exercise_id"],
            course_module__course_instance=instance).first()
        if not exercise:
            errors.append(
                _('Unknown exercise_id {id:d} in object {count:d}.')\
                    .format(id=submission_json["exercise_id"], count=count))
            continue

        # Use form to parse and validate object data.
        form = BatchSubmissionCreateAndReviewForm(submission_json,
            exercise=exercise)
        if form.is_valid():
            validated_forms.append(form)
        else:
            errors.append(
                _('Invalid fields in object {count:d}: {error}')\
                    .format(count=count,
                        error="\n".join(extract_form_errors(form))))

    if not errors:
        for form in validated_forms:
            sub = Submission.objects.create(exercise=form.exercise)
            sub.submitters = form.cleaned_data.get("students") \
                or (form.cleaned_data.get("students_by_student_id")
                    or form.cleaned_data.get("students_by_email"))
            sub.feedback = form.cleaned_data.get("feedback")
            sub.set_points(form.cleaned_data.get("points"),
                sub.exercise.max_points, no_penalties=True)
            sub.submission_time = form.cleaned_data.get("submission_time")
            sub.grading_time = timezone.now()
            sub.grader = form.cleaned_data.get("grader") or admin_profile
            sub.set_ready()
            sub.save()

    return errors
