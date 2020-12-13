from loguru import logger
import sys
import random

class Logger:
    
    def __init__(self):
        logger.info('Logger Ready!')
        logger.level("Inbound", no=34, icon="->", color="<yellow>")
        logger.level("Outgoing", no=33, icon="->", color="<green>")
    
    def error(self, message):
        logger.error(message)
        
    def outgoing(self, message):
        logger.log("Outgoing", message)
        
    def inbound(self, message):
        logger.log("Inbound", message)
        
    def info(self, message):
        logger.info(message)          
        
    def exception(self, message):
        logger.exception(message)    
    



