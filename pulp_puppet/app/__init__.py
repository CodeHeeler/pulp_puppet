from pulpcore.plugin import PulpPluginAppConfig


class PulpPuppetPluginAppConfig(PulpPluginAppConfig):
    name = 'pulp_puppet.app'
    label = 'pulp_puppet'
