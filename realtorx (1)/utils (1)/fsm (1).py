from rest_framework import status
from rest_framework.exceptions import ValidationError

from fsm_admin.mixins import FSMTransitionMixin


class SafeFSMTransitionMixin(FSMTransitionMixin):
    """Don't fail if validation error is raised inside transition check"""

    def _get_possible_transitions(self, obj):
        transitions = list(super()._get_possible_transitions(obj))
        for transition in transitions:
            try:
                [condition(obj) for condition in transition.conditions]
            except ValidationError:
                transitions.remove(transition)
        return transitions

    def _fsm_get_transitions(self, obj, request, **kwargs):
        transitions = super()._fsm_get_transitions(obj, request, **kwargs)
        for field, field_transitions in transitions.items():
            allowed_transitions = []
            while True:
                try:
                    field_transition = field_transitions.__next__()
                except ValidationError:
                    continue
                except StopIteration:
                    break

                allowed_transitions.append(field_transition)
            transitions[field] = allowed_transitions
        return transitions


class TransitionPermissionTestCaseMetaclass(type):
    @staticmethod
    def _collect_transitions(model):
        transitions = []
        for attr_name in dir(model):
            attr = getattr(model, attr_name, None)

            if hasattr(attr, "_django_fsm"):
                transitions.append(attr_name)

        return transitions

    @staticmethod
    def _annotate_test(klass, obj_status, transition):
        def test(self):
            obj = self.create_object(
                transition,
                **{
                    self.status_field.name: obj_status,
                }
            )

            result = self.do_transition(obj, transition)

            success, message = self.check_result(result, obj, transition)

            self.assertTrue(success, message)

        model = klass.model
        model_name = model._meta.model_name
        test_name = "test_{transition}_for_{obj_status}_{model_name}".format(
            transition=transition,
            obj_status=obj_status,
            model_name=model_name,
        )
        setattr(klass, test_name, test)

    def __new__(cls, name, bases, attrs):
        abstract = attrs.get("abstract", False)

        newclass = super().__new__(cls, name, bases, attrs)

        if abstract:
            return newclass

        newclass.transitions = cls._collect_transitions(newclass.model)
        newclass.status_field = getattr(
            newclass.model, newclass.transitions[0]
        )._django_fsm.field
        newclass.statuses = list(zip(*newclass.status_field.choices))[0]

        for obj_status in newclass.statuses:
            for transition in newclass.transitions:
                cls._annotate_test(newclass, obj_status, transition)

        return newclass


class TransitionPermissionsTestCaseMixin(
    object, metaclass=TransitionPermissionTestCaseMetaclass
):
    """
    TestCase mixin for dynamic transitions testing.
    All you need is to specify list of allowed transitions and user to be used.
    All tests will be generated automatically with correct output depending from user role.
    """

    abstract = True
    model = NotImplemented
    factory = NotImplemented

    def create_object(self, transition, **kwargs):
        return self.factory(**kwargs)

    def do_transition(self, obj, transition):
        raise NotImplementedError

    def check_result(self, result, obj, transition):
        allowed = (obj.status, transition) in self.ALLOWED_TRANSITION
        success = result.status_code == status.HTTP_200_OK
        forbidden = result.status_code == status.HTTP_423_LOCKED

        model_name = obj._meta.verbose_name

        if allowed and not success:
            mes = "Error on {transition} {status} {model_name} by {user_role}.\n{status_code}: {content}"
            return False, mes.format(
                transition=transition,
                status=obj.status,
                model_name=model_name,
                user_role=self.user_role,
                status_code=result.status_code,
                content=result.content,
            )

        if not allowed and success:
            mes = "Success for not allowed transition. {user_role} can't {transition} {status} {model_name}."
            return False, mes.format(
                user_role=self.user_role,
                transition=transition,
                status=obj.status,
                model_name=model_name,
            )

        if not allowed and not forbidden:
            mes = "Error on {transition} {status} {model_name} by {user_role}.\n{status_code}: {content}"
            return False, mes.format(
                transition=transition,
                status=obj.status,
                model_name=model_name,
                user_role=self.user_role,
                status_code=result.status_code,
                content=result.content,
            )

        return True, ""

    def get_extra_obj_attrs(self, **kwargs):
        attrs = {}
        attrs.update(kwargs)
        return attrs
