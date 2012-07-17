#!/usr/bin/python
#
# Copyright (c) 2012 Red Hat, Inc.
#
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import mock
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from uuid import uuid4
import importer_mocks

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/../../plugins/importers/")
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/../../plugins/distributors/")

from iso_distributor.distributor import ISODistributor, ISO_DISTRIBUTOR_TYPE_ID,\
    RPM_TYPE_ID, SRPM_TYPE_ID, DRPM_TYPE_ID, ERRATA_TYPE_ID, DISTRO_TYPE_ID, PKG_CATEGORY_TYPE_ID, PKG_GROUP_TYPE_ID
from yum_importer import importer_rpm

from pulp.plugins.model import RelatedRepository, Repository, Unit
from pulp.plugins.config import PluginCallConfiguration

import distributor_mocks
import rpm_support_base

class TestISODistributor(rpm_support_base.PulpRPMTests):

    def setUp(self):
        super(TestISODistributor, self).setUp()
        self.init()

    def tearDown(self):
        super(TestISODistributor, self).tearDown()
        self.clean()

    def init(self):
        self.temp_dir = tempfile.mkdtemp()
        #pkg_dir is where we simulate units actually residing
        self.pkg_dir = os.path.join(self.temp_dir, "packages")
        os.makedirs(self.pkg_dir)
        #publish_dir simulates /var/lib/pulp/published
        self.http_publish_dir = os.path.join(self.temp_dir, "publish", "http")
        os.makedirs(self.http_publish_dir)

        self.https_publish_dir = os.path.join(self.temp_dir, "publish", "https")
        os.makedirs(self.https_publish_dir)

        self.repo_working_dir = os.path.join(self.temp_dir, "repo_working_dir")
        os.makedirs(self.repo_working_dir)

        self.repo_iso_working_dir = os.path.join(self.temp_dir, "repo_working_dir", "isos")
        os.makedirs(self.repo_iso_working_dir)

        self.data_dir = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), "./data"))

    def clean(self):
        shutil.rmtree(self.temp_dir)

    def test_metadata(self):
        metadata = ISODistributor.metadata()
        self.assertEquals(metadata["id"], ISO_DISTRIBUTOR_TYPE_ID)
        for type in [RPM_TYPE_ID, SRPM_TYPE_ID, DRPM_TYPE_ID, ERRATA_TYPE_ID, DISTRO_TYPE_ID,
                     PKG_CATEGORY_TYPE_ID, PKG_GROUP_TYPE_ID]:
            self.assertTrue(type in metadata["types"])

    def test_export_rpm(self):
        feed_url = "file://%s/test_repo_for_export/" % (self.data_dir)
        repo = mock.Mock(spec=Repository)
        repo.working_dir = self.repo_working_dir
        repo.id = "test_repo_for_export"
        sync_conduit = importer_mocks.get_sync_conduit(existing_units=[], pkg_dir=self.pkg_dir)
        config = importer_mocks.get_basic_config(feed_url=feed_url)
        importerRPM = importer_rpm.ImporterRPM()
        status, summary, details = importerRPM.sync(repo, sync_conduit, config)
        self.assertTrue(summary is not None)
        self.assertTrue(details is not None)
        self.assertTrue(status)
        unit_key_a = {'id' : '','name' :'pulp-dot-2.0-test', 'version' :'0.1.2', 'release' : '1.fc11', 'epoch':'0', 'arch' : 'x86_64', 'checksumtype' : 'sha256',
                      'checksum': '435d92e6c09248b501b8d2ae786f92ccfad69fab8b1bc774e2b66ff6c0d83979', 'type_id' : 'rpm'}
        unit_a = Unit(RPM_TYPE_ID, unit_key_a, {}, '')
        unit_a.storage_path = "%s/pulp-dot-2.0-test/0.1.2/1.fc11/x86_64/435d92e6c09248b501b8d2ae786f92ccfad69fab8b1bc774e2b66ff6c0d83979/pulp-dot-2.0-test-0.1.2-1.fc11.x86_64.rpm" % self.pkg_dir
        unit_key_b = {'id' : '', 'name' :'pulp-test-package', 'version' :'0.2.1', 'release' :'1.fc11', 'epoch':'0','arch' : 'x86_64', 'checksumtype' :'sha256',
                      'checksum': '4dbde07b4a8eab57e42ed0c9203083f1d61e0b13935d1a569193ed8efc9ecfd7', 'type_id' : 'rpm', }
        unit_b = Unit(RPM_TYPE_ID, unit_key_b, {}, '')
        unit_b.storage_path = "%s/pulp-test-package/0.2.1/1.fc11/x86_64/4dbde07b4a8eab57e42ed0c9203083f1d61e0b13935d1a569193ed8efc9ecfd7/pulp-test-package-0.2.1-1.fc11.x86_64.rpm" % self.pkg_dir
        unit_key_c = {'id' : '', 'name' :'pulp-test-package', 'version' :'0.3.1', 'release' :'1.fc11', 'epoch':'0','arch' : 'x86_64', 'checksumtype' :'sha256',
                      'checksum': '6bce3f26e1fc0fc52ac996f39c0d0e14fc26fb8077081d5b4dbfb6431b08aa9f', 'type_id' : 'rpm', }
        unit_c = Unit(RPM_TYPE_ID, unit_key_c, {}, '')
        unit_c.storage_path =  "%s/pulp-test-package/0.3.1/1.fc11/x86_64/6bce3f26e1fc0fc52ac996f39c0d0e14fc26fb8077081d5b4dbfb6431b08aa9f/pulp-test-package-0.3.1-1.fc11.x86_64.rpm" % self.pkg_dir
        existing_units = []
        for unit in [unit_a, unit_b, unit_c]:
            existing_units.append(unit)
        symlink_dir = "%s/%s" % (self.repo_working_dir, repo.id)
        iso_distributor = ISODistributor()
        publish_conduit = distributor_mocks.get_publish_conduit(existing_units=existing_units, pkg_dir=self.pkg_dir)
        config = distributor_mocks.get_basic_config(https_publish_dir=self.https_publish_dir, http=False, https=True)
        print symlink_dir
        status, errors = iso_distributor._export_rpms(existing_units, symlink_dir)
        print status, errors
        self.assertTrue(status)
        self.assertEquals(len(os.listdir(symlink_dir)), 4)