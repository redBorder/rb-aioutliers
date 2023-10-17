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

import uuid
import boto3

class S3:
    """
    Initialize the S3 class with the necessary AWS credentials and bucket information.

    Args:
        access_key (str): AWS access key.
        secret_key (str): AWS secret key.
        region_name (str): AWS region name.
        bucket_name (str): S3 bucket name.
    """
    def __init__(self, access_key, secret_key, region_name, bucket_name, endpoint_url):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region_name = region_name
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
            endpoint_url=endpoint_url
        )
        self.s3_path = "rbaioutliers/"
        self.unique_s3_key = str(uuid.uuid4())
    
    """
    Upload a local file to an S3 bucket.

    Args:
        local_file_path (str): The path to the local file you want to upload.
        s3_key (str): The key under which the file will be stored in S3.
    """
    def upload_file(self, local_file_path, s3_key):
        try:
            self.s3_client.upload_file(local_file_path, self.bucket_name, s3_key)
            print(f"Uploaded {local_file_path} to S3")
        except Exception as e:
            print(f"Error uploading file to S3: {str(e)}")

    """
    Download a file from an S3 bucket to a local directory.

    Args:
        s3_key (str): The key of the file in S3.
        local_file_path (str): The local path where the file will be saved.
    """
    def download_file(self, s3_key, local_file_path):
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_file_path)
            print(f"Downloaded {s3_key} from S3 to {local_file_path}")
        except Exception as e:
            print(f"Error downloading file from S3: {str(e)}")

    """
    List all objects in the S3 bucket.

    This method lists all objects in the S3 bucket and prints their keys.
    """
    def list_objects(self):
        try:
            response = self.s3_client.list_objects(Bucket=self.bucket_name)
            objects = [obj['Key'] for obj in response.get('Contents', [])]
            print("Objects in the S3 bucket:")
            for obj in objects:
                print(obj)
        except Exception as e:
            print(f"Error listing objects in S3 bucket: {str(e)}")

    """
    Delete an object from the S3 bucket.

    Args:
        s3_key (str): The key of the object to be deleted.
    """
    def delete_object(self, s3_key):
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            print(f"Deleted {s3_key} from S3")
        except Exception as e:
            print(f"Error deleting object from S3: {str(e)}")
