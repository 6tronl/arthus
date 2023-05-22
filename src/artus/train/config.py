from detectron2 import model_zoo
import yaml
import os


def read_config(config_path):
    '''
    Read a yaml file used to config a model for training or inference.
    # Input :
    - config_path : the path to a config file in yaml format
    # Output : 
    - a python object 
    '''
    with open(config_path) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config
	
def check_logs(config_path):
    '''
    Check if the config file already contains path to a log directory (which include a checkpoint to a model)
    # Input :
    - config_path : the path to a config file in yaml format
    # Output : 
    - Returns true if the config file includes path to a log directory, false otherwise.
    '''
    config = read_config(config_path)
    if config['LOGS']['CHECKPOINT']:
        check_logs = True
    else:
        check_logs = False
    return check_logs

def add_config(cfg, config_path, device, train_dataset, test_dataset, output_dir=None, mode=['train', 'inference']):
    """
    Add config for DL model coming from a yaml config file.
    """
    config = read_config(config_path)
        
    cfg.merge_from_file(model_zoo.get_config_file(config['MODEL']['URL']))

    if mode == 'train':
        cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(config['MODEL']['URL'])
    elif mode == 'inference':
        cfg.MODEL.WEIGHTS = config['LOGS']['CHECKPOINT']

    cfg.DATASETS.TRAIN = train_dataset
    cfg.DATASETS.TEST = test_dataset

    cfg.TEST.EVAL_PERIOD = config['TEST']['EVAL_PERIOD']
    cfg.DATALOADER.NUM_WORKERS = config['DATALOADER']['NUM_WORKERS']
    cfg.SOLVER.IMS_PER_BATCH = config['SOLVER']['IMS_PER_BATCH']
    cfg.SOLVER.BASE_LR = config['SOLVER']['BASE_LR']
    cfg.SOLVER.MAX_ITER = config['SOLVER']['MAX_ITER']
    cfg.SOLVER.STEPS = config['SOLVER']['STEPS']
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = config['MODEL']['ROI_HEADS']['NUM_CLASSES']
    cfg.SOLVER.REFERENCE_WORLD_SIZE = 1
    cfg.MODEL_DEVICE = device
    cfg.OUTPUT_DIR = output_dir
    cfg.INPUT.MIN_SIZE_TRAIN = (config['INPUT']['MIN_SIZE_TRAIN'],)
    cfg.INPUT.MAX_SIZE_TRAIN = config['INPUT']['MAX_SIZE_TRAIN']
    cfg.INPUT.MIN_SIZE_TEST = config['INPUT']['MIN_SIZE_TEST']
    cfg.INPUT.MAX_SIZE_TEST = config['INPUT']['MAX_SIZE_TEST']
    return cfg
    
 
