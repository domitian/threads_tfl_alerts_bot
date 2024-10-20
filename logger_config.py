import logging

def setup_logger():
    logging.basicConfig(filename='tfl_api.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)

logger = setup_logger()
