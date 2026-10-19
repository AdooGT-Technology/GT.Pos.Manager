"""
GT-POS Client Configuration
"""

import json
import os

class ClientConfig:
    CONFIG_FILE = "client_config.json"
    
    SERVER_HOST = "127.0.0.1"
    SERVER_PORT = 44556
    HOST_ID = 1
    HOST_NUMBER = 1
    HOST_NAME = "PC-01"
    
    LOCK_DESKTOP = True
    BLOCK_TASK_MANAGER = True
    AUTO_RECONNECT = True
    RECONNECT_INTERVAL = 5  # ثوان
    
    @classmethod
    def load(cls):
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                for key, value in data.items():
                    if hasattr(cls, key):
                        setattr(cls, key, value)
            except:
                pass
    
    @classmethod
    def save(cls):
        data = {
            'SERVER_HOST': cls.SERVER_HOST,
            'SERVER_PORT': cls.SERVER_PORT,
            'HOST_ID': cls.HOST_ID,
            'HOST_NUMBER': cls.HOST_NUMBER,
            'HOST_NAME': cls.HOST_NAME,
            'LOCK_DESKTOP': cls.LOCK_DESKTOP,
            'BLOCK_TASK_MANAGER': cls.BLOCK_TASK_MANAGER,
        }
        with open(cls.CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)