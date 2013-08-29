# -*- coding: utf-8 -*-
#
# Copyright © 2013 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

from gettext import gettext as _
import logging
import os
import shutil
import tarfile

from pulp.plugins.distributor import Distributor
from pulp.server.db.model.criteria import UnitAssociationCriteria

from pulp_puppet.common import constants

ERROR_MESSAGE_PATH = 'one or more units contains a path outside its base extraction path'
_LOGGER = logging.getLogger(__name__)


def entry_point():
    """
    Entry point that pulp platform uses to load the distributor

    :return: distributor class and its config
    :rtype:  Distributor, {}
    """
    # there is never a default or global config for this distributor
    return PuppetModuleInstallDistributor, {}


class PuppetModuleInstallDistributor(Distributor):
    def __init__(self):
        super(PuppetModuleInstallDistributor, self).__init__()
        self.detail_report = DetailReport()

    @classmethod
    def metadata(cls):
        return {
            'id': constants.INSTALL_DISTRIBUTOR_TYPE_ID,
            'display_name': _('Puppet Install Distributor'),
            'types': [constants.TYPE_PUPPET_MODULE]
        }

    def validate_config(self, repo, config, config_conduit):
        """
        :param repo:            metadata describing the repository to which the
                                configuration applies
        :type  repo:            pulp.plugins.model.Repository

        :param config:          plugin configuration instance; the proposed repo
                                configuration is found within
        :type  config:          pulp.plugins.config.PluginCallConfiguration
        :param config_conduit:  Configuration Conduit;
        :type  config_conduit:  pulp.plugins.conduits.repo_config.RepoConfigConduit
        :return: tuple of (bool, str) to describe the result
        :rtype:  tuple
        """
        path = config.get(constants.CONFIG_INSTALL_PATH)
        if not isinstance(path, basestring):
            # path not here, nothing else to validate
            return True, None
        if not os.path.isabs(path):
            return False, _('install path is not absolute')
        if not os.path.isdir(path):
            return False, _('install path is not an existing directory')
        # we need X to get directory listings
        if not os.access(path, os.R_OK|os.W_OK|os.X_OK):
            return False, _('the current user does not have permission to read '
                            'and write files in the destination directory')

        return True, None

    def publish_repo(self, repo, publish_conduit, config):
        """
        Publish the repository by "installing" each puppet module into the given
        destination directory. This effectively means extracting each module's
        tarball in that directory.

        :param repo:            metadata describing the repository
        :type  repo:            pulp.plugins.model.Repository
        :param publish_conduit: provides access to relevant Pulp functionality
        :type  publish_conduit: pulp.plugins.conduits.repo_publish.RepoPublishConduit
        :param config:          plugin configuration
        :type  config:          pulp.plugins.config.PluginConfiguration

        :return: report describing the publish run
        :rtype:  pulp.plugins.model.PublishReport
        """
        # get dir from config
        destination = config.get(constants.CONFIG_INSTALL_PATH)
        if not destination:
            return publish_conduit.build_failure_report('install path not provided',
                                                        self.detail_report.report)

        units = publish_conduit.get_units(UnitAssociationCriteria([constants.TYPE_PUPPET_MODULE]))

        duplicate_units = self._find_duplicate_names(units)
        if duplicate_units:
            for unit in duplicate_units:
                self.detail_report.error(unit.unit_key,
                                         'another unit in this repo also has this name')
            return publish_conduit.build_failure_report('duplicate unit names', self.detail_report.report)

        # check for unsafe paths in tarballs, and fail early if problems are found
        self._check_for_unsafe_archive_paths(units, destination)
        if self.detail_report.has_errors:
            return publish_conduit.build_failure_report('failed', self.detail_report.report)

        # clear out pre-existing contents
        try:
            self._clear_destination_directory(destination)
        except (IOError, OSError), e:
            return publish_conduit.build_failure_report(
                'failed to clear destination directory: %s' % str(e),
                self.detail_report.report)

        # actually publish
        for unit in units:
            try:
                archive = tarfile.open(unit.storage_path)
                try:
                    archive.extractall(destination)
                    self._rename_directory(unit, destination, archive.getnames())
                finally:
                    archive.close()
                self.detail_report.success(unit.unit_key)
            except (OSError, IOError, ValueError), e:
                self.detail_report.error(unit.unit_key, str(e))

        # return some kind of report
        if self.detail_report.has_errors:
            return publish_conduit.build_failure_report('failed', self.detail_report.report)
        else:
            return publish_conduit.build_success_report('success', self.detail_report.report)

    @staticmethod
    def _find_duplicate_names(units):
        """
        Returns a list of units that have the same name as at least one other
        unit in this repository. This is a problem because in order to "install"
        these modules, they must be extracted into the destination directory
        and renamed to just the "name" portion of their unit key. Multiple units
        with the name name will conflict on the filesystem.

        :param units:   iterable of all units being published
        :type  units:   iterable

        :return:    list of units that have conflicting names
        :rtype:     list
        """
        names = {}
        for unit in units:
            name = unit.unit_key['name']
            if name not in names:
                names[name] = 1
            else:
                names[name] = names[name] + 1

        duplicates = set()
        for name, count in names.iteritems():
            if count > 1:
                duplicates.add(name)
        return [unit for unit in units if unit.unit_key['name'] in duplicates]

    @staticmethod
    def _rename_directory(unit, destination, names):
        """
        Given a list of names from a unit's tarball and the destination, figure
        out the name of the directory that was extracted, and then move it to
        the name that puppet expects.

        :param unit:        unit whose tarball was extracted at the destination
        :type  unit:        pulp.plugins.model.AssociatedUnit
        :param destination: absolute path to the destination where modules should
                            be installed
        :type  destination: str
        :param names:       list of paths (relative or absolute) to files that
                            are contained in the archive that was just extracted.
        :type  names:       list

        :raise:     IOError, ValueError
        """
        if not destination.endswith('/'):
            destination += '/'
        dest_length = len(destination)

        dir_names = set([os.path.join(destination, name)[dest_length:].split('/')[0] for name in names])
        if len(dir_names) != 1:
            raise ValueError('too many directories extracted')

        before = os.path.join(destination, dir_names.pop())
        after = os.path.join(destination, unit.unit_key['name'])
        shutil.move(before, after)

    def _check_for_unsafe_archive_paths(self, units, destination):
        """
        Check the paths of files in each tarball to make sure none include path
        components, such as "../", that would cause files to be placed outside of
        the destination directory. Adds errors to the detail report for each unit
        that has one or more offending paths.

        :param units:       list of pulp.plugins.model.AssociatedUnit whose
                            tarballs should be checked for unsafe paths
        :type  units:       list
        :param destination: absolute path to the destination where modules should
                            be installed
        :type  destination: str
        """
        for unit in units:
            try:
                archive = tarfile.open(unit.storage_path)
                try:
                    if not self._archive_paths_are_safe(destination, archive):
                        self.detail_report.error(unit.unit_key, ERROR_MESSAGE_PATH)
                finally:
                    archive.close()
            except (OSError, IOError), e:
                self.detail_report.error(unit.unit_key, str(e))

    @staticmethod
    def _archive_paths_are_safe(destination, archive):
        """
        Checks a tarball archive for paths that include components such as "../"
        that would cause files to be placed outside of the destination_path.

        :param destination: absolute path to the destination where modules should
                            be installed
        :type  destination: str
        :param archive:     tarball archive that should be checked
        :type  archive      tarfile.TarFile

        :return:    True iff all paths in the archive are safe, else False
        :rtype:     bool
        """
        for name in archive.getnames():
            result = os.path.normpath(os.path.join(destination, name))
            if not destination.endswith('/'):
                destination += '/'
            if not result.startswith(destination):
                return False
        return True

    @staticmethod
    def _clear_destination_directory(destination):
        """
        deletes every directory found in the given destination

        :param destination: absolute path to the destination where modules should
                            be installed
        :type  destination: str
        """
        for directory in os.listdir(destination):
            path = os.path.join(destination, directory)
            if os.path.isdir(path):
                shutil.rmtree(path)


class DetailReport(object):
    """
    convenience class to manage the structure of the "detail" report
    """
    def __init__(self):
        self.report = {
            'success_unit_keys': [],
            'errors': [],
        }

    def success(self, unit_key):
        """
        Call for each unit that is successfully published. This adds that unit
        key to the report.

        :param unit_key:    unit key for a successfully published unit
        :type  unit_key:    dict
        """
        self.report['success_unit_keys'].append(unit_key)

    def error(self, unit_key, error_message):
        """
        Call for each unit that has an error during publish. This adds that unit
        key to the report.

        :param unit_key:        unit key for unit that had an error during publish
        :type  unit_key:        dict
        :param error_message:   error message indicating what went wrong for this
                                particular unit
        """
        self.report['errors'].append((unit_key, error_message))

    @property
    def has_errors(self):
        """
        :return:    True iff this report has one or more errors, else False
        :rtype:     bool
        """
        return bool(self.report['errors'])
