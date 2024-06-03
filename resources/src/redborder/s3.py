# Copyright (C) 2023 Eneo Tecnologia S.L.
#
# Authors:
# Miguel Álvarez Adsuara <malvarez@redborder.com>
# Pablo Rodriguez Flores <prodriguez@redborder.com>
#
# This program is free software: you can redistribute it and/or modify it under the terms of the
# GNU Affero General Public License as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along with this program.
# If not, see <https://www.gnu.org/licenses/>.


import uuid
import boto3
from resources.src.logger.logger import logger

class S3:
    def __init__(self, access_key, secret_key, region_name, bucket_name, endpoint_url):
        """
        Initialize the S3 class with the necessary AWS credentials and bucket information.
        """
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
            endpoint_url=endpoint_url
        )
        self.bucket_name = bucket_name

    def upload_file(self, local_file_path, s3_key):
        """
        Upload a local file to an S3 bucket.

        Args:
            local_file_path (str): The path to the local file you want to upload.
            s3_key (str): The key under which the file will be stored in S3.
        """
        try:
            self.s3_client.upload_file(local_file_path, self.bucket_name, s3_key)
            logger.logger.info(f"Uploaded {local_file_path} to S3")
        except Exception as e:
            logger.logger.error(f"Error uploading file to S3: {str(e)}")

    def download_file(self, s3_key, local_file_path):
        """
        Download a file from an S3 bucket to a local directory.

        Args:
            s3_key (str): The key of the file in S3.
            local_file_path (str): The local path where the file will be saved.
        """
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_file_path)
            logger.logger.info(f"Downloaded {s3_key} from S3 to {local_file_path}")
        except Exception as e:
            logger.logger.error(f"Error downloading file from S3: {str(e)}")


    def list_objects(self):
        """
        List all objects in the S3 bucket.

        This method lists all objects in the S3 bucket and prints their keys.
        """
        try:
            response = self.s3_client.list_objects(Bucket=self.bucket_name)
            objects = [obj['Key'] for obj in response.get('Contents', [])]
            logger.logger.info("Objects in the S3 bucket:")
            for obj in objects:
                logger.logger.info(obj)
        except Exception as e:
            logger.logger.error(f"Error listing objects in S3 bucket: {str(e)}")

    def list_objects_in_folder(self, folder_prefix):
        """
        List all objects in the S3 bucket in a specific prefix.

        This method lists all objects in the S3 bucket and prints their keys.
        """
        try:
            response = self.s3_client.list_objects(Bucket=self.bucket_name, Prefix=folder_prefix)
            objects = [obj['Key'] for obj in response.get('Contents', [])]
            return objects
        except Exception as e:
            logger.logger.error(f"Error listing objects in S3 folder '{folder_prefix}': {str(e)}")
            return []

    def delete_object(self, s3_key):
        """
        Delete an object from the S3 bucket.

        Args:
            s3_key (str): The key of the object to be deleted.
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.logger.info(f"Deleted {s3_key} from S3")
        except Exception as e:
            logger.logger.error(f"Error deleting object from S3: {str(e)}")

    def exists(self, s3_key):
        """
        Check if a file exists in the S3 bucket.

        Args:
            s3_key (str): The key of the file to check in S3.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except self.s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.logger.error(f"Error checking file existence: {str(e)}")
                return False