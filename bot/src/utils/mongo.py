"""
Odoaldo-DiscordBot
Copyright (C) 2021  Massimo Pavoni

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from json import load as json_load
from logging import getLogger
from os import listdir as os_listdir
from os.path import join as path_join

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Setting up util logger
logger = getLogger(__name__.split('.', 1)[-1])


class MongoUtil(object):
    """
    Mongo utility singleton.
    """
    __instance = None
    __mongo_client = None
    __db = None

    def __new__(cls, mongo_uri=None):
        if cls.__instance is None:
            logger.info("Creating mongo client singleton instance")
            cls.__instance = super(MongoUtil, cls).__new__(cls)
            cls.__mongo_client = MongoClient(mongo_uri, timeoutMS=8000)
            # Already prepare default database
            cls.__db = cls.__mongo_client['odoaldo']
        return cls.__instance

    def ping(self):
        try:
            logger.info("Pinging mongo instance")
            self.__mongo_client.admin.command('ping')
            return ''
        except ConnectionFailure as error:
            return error

    def db(self):
        return self.__db

    def load_init_data(self, reset=False):
        logger.info(
            "Resetting mongo database to init data" if reset else "Initializing mongo database with missing data")
        init_data_path = path_join('bot', 'src', 'init_data')
        for file in os_listdir(init_data_path):
            collection = file.replace('.json', '')
            if collection not in self.__db.list_collection_names() or reset:
                with open(path_join(init_data_path, file), 'r', encoding='utf-8') as f:
                    data = json_load(f)
                logger.info(f"Resetting {collection} collection")
                self.__db[collection].drop()
                self.__db[collection].insert_many(data)
