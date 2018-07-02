"""
Check `Plugin Writer's Guide`_ and `pulp_example`_ plugin
implementation for more details.

.. _Plugin Writer's Guide:
    http://docs.pulpproject.org/en/3.0/nightly/plugins/plugin-writer/index.html

.. _pulp_example:
    https://github.com/pulp/pulp_example/
"""
from rest_framework import serializers
from pulpcore.plugin import serializers as platform

from . import models


class PuppetContentSerializer(platform.ContentSerializer):
    """
    A Serializer for PuppetContent.

    Add serializers for the new fields defined in PuppetContent and
    add those fields to the Meta class keeping fields from the parent class as well.

    For example::

    field1 = serializers.TextField()
    field2 = serializers.IntegerField()
    field3 = serializers.CharField()

    class Meta:
        fields = platform.ContentSerializer.Meta.fields + ('field1', 'field2', 'field3')
        model = models.PuppetContent
    """

    class Meta:
        fields = platform.ContentSerializer.Meta.fields
        model = models.PuppetContent


class PuppetRemoteSerializer(platform.RemoteSerializer):
    """
    A Serializer for PuppetRemote.

    Add any new fields if defined on PuppetRemote.
    Similar to the example above, in PuppetContentSerializer.
    Additional validators can be added to the parent validators list

    For example::

    class Meta:
        validators = platform.RemoteSerializer.Meta.validators + [myValidator1, myValidator2]
    """

    class Meta:
        fields = platform.RemoteSerializer.Meta.fields
        model = models.PuppetRemote


class PuppetPublisherSerializer(platform.PublisherSerializer):
    """
    A Serializer for PuppetPublisher.

    Add any new fields if defined on PuppetPublisher.
    Similar to the example above, in PuppetContentSerializer.
    Additional validators can be added to the parent validators list

    For example::

    class Meta:
        validators = platform.PublisherSerializer.Meta.validators + [myValidator1, myValidator2]
    """

    class Meta:
        fields = platform.PublisherSerializer.Meta.fields
        model = models.PuppetPublisher
