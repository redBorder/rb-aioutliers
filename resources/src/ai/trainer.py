# Copyright (C) 2023 Eneo Tecnologia S.L.
#
# Authors :
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

import os
'''
Start of important OS Variables
'''
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
'''
End of important OS Variables
'''
import sys
import datetime
import configparser
from datetime import datetime
from src.ai.outliers import Autoencoder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

"""
This module extends the Autoencoder class to allow further training of the model.
"""

class Trainer(Autoencoder):
    """
    Class for training the autoencoder model for anomaly detection.

    Args:
        model_file (str): Path to model's .keras file.
        model_config_file (dict): Path to model's .ini file.
    """

    def __init__(self, model_file, model_config_file):
        """
        Class initialization.

        Args:
            model_file (str): Path to model's .keras file.
            model_config_file (dict): Path to model's .ini file.
        """
        super().__init__(model_file, model_config_file)
        self.model_file = model_file
        self.model_config_file = model_config_file

    def save_model(self, save_model_file, save_config_file):
        """
        Saves the current model and config on the given paths.

        Args:
            save_model_file (str): Path to where the model's .keras should be saved.
            save_config_file (str): Path to where the model's .ini should be saved.
        """
        if os.path.exists(save_model_file):
            if not os.access(save_model_file, os.W_OK):
                raise PermissionError(f"Permission denied: Cannot overwrite '{save_model_file}'")
        if os.path.exists(save_config_file):
            if not os.access(save_config_file, os.W_OK):
                raise PermissionError(f"Permission denied: Cannot overwrite '{save_config_file}'")
        self.model.save(save_model_file)
        new_model_config = configparser.ConfigParser()
        new_model_config.add_section('Columns')
        columns_section = new_model_config['Columns']
        columns_section['METRICS'] = ', '.join(self.METRICS)
        columns_section['TIMESTAMP'] = ', '.join(self.TIMESTAMP)
        columns_section['GRANULARITIES'] = ', '.join(self.GRANULARITIES)
        new_model_config.add_section('General')
        general_section = new_model_config['General']
        general_section['AVG_LOSS'] = str(self.AVG_LOSS)
        general_section['STD_LOSS'] = str(self.STD_LOSS)
        general_section['WINDOW_SIZE'] = str(self.WINDOW_SIZE)
        general_section['NUM_WINDOWS'] = str(self.NUM_WINDOWS)
        general_section['LOSS_MULT_1'] = str(self.LOSS_MULT_1)
        general_section['LOSS_MULT_2'] = str(self.LOSS_MULT_2)
        with open(save_config_file, 'w') as configfile:
            new_model_config.write(configfile)

    def data_augmentation(self, data):
        """
        TODO
        Makes artificial data by adding different kinds of noise to it.

        Args:
            data (numpy ndarray): original data to be fed to the model.
        
        Returns:
            augmented (numpy ndarray): augmented data.
        """
        return data

    def prepare_data_for_training(self, data, augment = False):
        """
        Prepares data to be used for training the model.

        Args:
            data (numpy ndarray): data to be used for training.
            augment (boolean): set to True to generate more data for training.
        
        Returns:
            prep_data (numpy ndarray): transformed data for its use in the model.
        """
        prep_data = self.rescale(data)
        if augment:
            #TODO actually augment data
            prep_data = self.data_augmentation(prep_data)
        else:
            prep_data = self.slice(prep_data)
        return prep_data

    def train(self, raw_data, epochs=20, batch_size=32, backup_path=None):
        """
        Given a druid query response, it is fed to the model for training.

        Args:
            raw_data (json): response form a druid query.
            epochs (int): how many times should the model train on the data.
            batch_size (int): how many slices should the model take at once
            for training.
            backup_path (None or str): path to where the backups should be saved.
        """
        if backup_path is None:
            backup_path = "./backups/"
        date = datetime.now().strftime("%y-%m-%dT%H:%M")
        self.save_model(f"{backup_path}{date}.keras",f"{backup_path}{date}.ini")
        data = self.input_json(raw_data)[0]
        prep_data = self.prepare_data_for_training(data)
        self.model.fit(prep_data, epochs = epochs, batch_size = batch_size, verbose = 0)
        loss = self.model_loss(prep_data, self.model.predict(prep_data), single_value=False).numpy()
        self.AVG_LOSS = 0.9*self.AVG_LOSS + 0.1*loss.mean()
        self.STD_LOSS = 0.9*self.AVG_LOSS + 0.1*loss.std()
        self.save_model(self.model_file ,self.model_config_file)
