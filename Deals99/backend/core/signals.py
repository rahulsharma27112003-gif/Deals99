from django.db import connection
from django.db.models.fields.files import FieldFile
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog
from .middleware import get_current_user, get_current_request

# Simple in-memory cache to hold pre-save state for comparison in post_save
_PRE_SAVE_CACHE = {}


def _audit_log_table_exists():
    try:
        return 'core_auditlog' in connection.introspection.table_names()
    except Exception:
        return False



def _make_key(instance):
    return f"{instance.__class__.__module__}.{instance.__class__.__name__}:{getattr(instance, 'pk', None)}"


def _serialize_value(value):
    from datetime import date, datetime, time
    from decimal import Decimal

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, FieldFile):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    return value


def _serialize_model_dict(data):
    return {k: _serialize_value(v) for k, v in (data or {}).items()}


@receiver(pre_save)
def _capture_pre_save(sender, instance, **kwargs):
    try:
        if instance.pk is None:
            return
        # avoid capturing AuditLog itself
        if sender._meta.model_name == 'auditlog':
            return
        old = sender.objects.filter(pk=instance.pk).first()
        if old is not None:
            _PRE_SAVE_CACHE[_make_key(instance)] = model_to_dict(old)
    except Exception:
        return


@receiver(post_save)
def _record_post_save(sender, instance, created, **kwargs):
    try:
        if sender._meta.model_name == 'auditlog':
            return

        if not _audit_log_table_exists():
            return

        key = _make_key(instance)
        new = _serialize_model_dict(model_to_dict(instance))
        old = _serialize_model_dict(_PRE_SAVE_CACHE.pop(key, None))

        if created:
            changes = {'new': new}
            action = AuditLog.ACTION_CREATE
        else:
            # compute simple diff
            changes = {}
            if old is None:
                changes = {'new': new}
            else:
                changed = {}
                for k, v in new.items():
                    if old.get(k) != v:
                        changed[k] = {'old': old.get(k), 'new': v}
                changes = changed
            action = AuditLog.ACTION_UPDATE

        actor = get_current_user()
        request = get_current_request()
        ip = None
        if request is not None:
            ip = request.META.get('REMOTE_ADDR')

        AuditLog.objects.create(
            action=action,
            content_type=ContentType.objects.get_for_model(instance.__class__),
            object_id=str(getattr(instance, 'pk', '')),
            object_repr=str(instance),
            changes=changes or None,
            actor=actor if getattr(actor, 'is_authenticated', False) else None,
            ip_address=ip,
        )
    except Exception:
        # never raise from a signal
        return


@receiver(post_delete)
def _record_post_delete(sender, instance, **kwargs):
    try:
        if sender._meta.model_name == 'auditlog':
            return

        if not _audit_log_table_exists():
            return

        data = _serialize_model_dict(model_to_dict(instance))
        actor = get_current_user()
        request = get_current_request()
        ip = None
        if request is not None:
            ip = request.META.get('REMOTE_ADDR')

        AuditLog.objects.create(
            action=AuditLog.ACTION_DELETE,
            content_type=ContentType.objects.get_for_model(instance.__class__),
            object_id=str(getattr(instance, 'pk', '')),
            object_repr=str(instance),
            changes={'old': data},
            actor=actor if getattr(actor, 'is_authenticated', False) else None,
            ip_address=ip,
        )
    except Exception:
        return
