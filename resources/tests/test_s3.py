# Copyright (C) 2023 Eneo Tecnologia S.L.
#
# Authors :
# Miguel Álvarez Adsuara <malvarez@redborder.com>
# Pablo Rodriguez Flores <prodriguez@redborder.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import tempfile
import os, sys
import boto3
from moto import mock_s3
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.redborder.s3 import S3

@mock_s3
class TestS3Methods(unittest.TestCase):
    def setUp(self):
        self.access_key = 'mock_access_key'
        self.secret_key = 'mock_secret_key'
        self.region_name = 'us-west-1'
        self.bucket_name = 'test-bucket'
        self.s3_path = 'rbaioutliers/'
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name,
            endpoint_url=None
        )

        self.s3_client.create_bucket(Bucket=self.bucket_name, CreateBucketConfiguration={'LocationConstraint': self.region_name})

        self.s3 = S3(self.access_key, self.secret_key, self.region_name, self.bucket_name, None)

    def test_upload_and_download_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b'Test data')
            temp_file_path = temp_file.name

        s3_key = f'{self.s3_path}{uuid.uuid4()}'

        self.s3.upload_file(temp_file_path, s3_key)

        download_file_path = tempfile.NamedTemporaryFile(delete=False).name
        self.s3.download_file(s3_key, download_file_path)

        with open(download_file_path, 'rb') as downloaded_file:
            self.assertEqual(downloaded_file.read(), b'Test data')

        os.remove(temp_file_path)
        os.remove(download_file_path)

    def test_list_objects(self):
        self.s3.list_objects()

    def test_delete_object(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b'Test data')
            temp_file_path = temp_file.name

        s3_key = f'{self.s3_path}{uuid.uuid4()}'

        self.s3.upload_file(temp_file_path, s3_key)

        self.s3.delete_object(s3_key)

        objects = self.s3_client.list_objects(Bucket=self.bucket_name).get('Contents', [])
        self.assertNotIn(s3_key, [obj['Key'] for obj in objects])

        os.remove(temp_file_path)

    def tearDown(self):
        objects = self.s3_client.list_objects(Bucket=self.bucket_name).get('Contents', [])
        for obj in objects:
            s3_key = obj['Key']
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)        
        self.s3_client.delete_bucket(Bucket=self.bucket_name)

if __name__ == '__main__':
    unittest.main()