import os
from pathlib import Path
from yamlwidgets import YamlWidgets
from pytimeloop.app import ModelApp, MapperApp
from pytimeloop.accelergy_interface import invoke_accelergy
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO

import logging, sys
logger = logging.getLogger('pytimeloop')
formatter = logging.Formatter(
    '[%(levelname)s] %(asctime)s - %(name)s - %(message)s')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class ConfigRegistry:
    DESIGN_DIR = Path('designs')
    
    # BASELINE
    BASELINE_DIR = DESIGN_DIR / 'baseline'
    BASELINE_ARCH = BASELINE_DIR / 'arch/2level.arch.yaml'
    BASELINE_COMPONENTS = BASELINE_DIR / 'components'
    BASELINE_MAPPER = BASELINE_DIR / 'mapper/mapper.yaml'
    BASELINE_SPARSE_OPT = BASELINE_DIR / 'sparse-opt'
    BASELINE_CONSTRAINTS_SUPPORT = BASELINE_DIR / 'constraints/constraints_support.yaml'
    BASELINE_CONSTRAINTS_OUTPUT = BASELINE_DIR / 'constraints/constraints_output.yaml'
    BASELINE_PROB_L1_SUPPORT = BASELINE_DIR / 'prob/GCN_layer1_support.yaml'
    BASELINE_PROB_L1_OUTPUT = BASELINE_DIR / 'prob/GCN_layer1_output.yaml'
    BASELINE_PROB_L2_SUPPORT = BASELINE_DIR / 'prob/GCN_layer2_support.yaml'
    BASELINE_PROB_L2_OUTPUT = BASELINE_DIR / 'prob/GCN_layer2_output.yaml'
    
    # EnGN
    ENGN_DIR = DESIGN_DIR / 'EnGN'
    ENGN_ARCH = ENGN_DIR / 'arch/EnGN.yaml'
    ENGN_COMPONENTS = ENGN_DIR / 'arch/components'
    ENGN_MAPPER = ENGN_DIR / 'mapper/mapper.yaml'
    ENGN_SPARSE_OPT = ENGN_DIR / 'sparse-opt'
    ENGN_CONSTRAINTS_SUPPORT = ENGN_DIR / 'constraints/constraints_support.yaml'
    ENGN_CONSTRAINTS_OUTPUT = ENGN_DIR / 'constraints/constraints_output.yaml'
    ENGN_PROB_L1_SUPPORT = ENGN_DIR / 'prob/GCN_layer1_support.yaml'
    ENGN_PROB_L1_OUTPUT = ENGN_DIR / 'prob/GCN_layer1_output.yaml'
    ENGN_PROB_L2_SUPPORT = ENGN_DIR / 'prob/GCN_layer2_support.yaml'
    ENGN_PROB_L2_OUTPUT = ENGN_DIR / 'prob/GCN_layer2_output.yaml'

def load_config(*paths):
    yaml = YAML(typ='safe')
    yaml.version = (1, 2)
    total = None
    def _collect_yaml(yaml_str, total):
        new_stuff = yaml.load(yaml_str)
        if total is None:
            return new_stuff

        for key, value in new_stuff.items():
            if key == 'compound_components' and key in total:
                total['compound_components']['classes'] += value['classes']
            elif key in total:
                raise RuntimeError(f'overlapping key: {key}')
            else:
                total[key] = value
        return total

    for path in paths:
        if isinstance(path, str):
            total = _collect_yaml(path, total)
            continue
        elif path.is_dir():
            for p in path.glob('*.yaml'):
                with p.open() as f:
                    total = _collect_yaml(f.read(), total)
        else:
            with path.open() as f:
                total = _collect_yaml(f.read(), total)
    return total

def load_config_str(*paths):
    total = ''
    for path in paths:
        if isinstance(path, str):
            return path
        elif path.is_dir():
            for p in path.glob('*.yaml'):
                with p.open() as f:
                    total += f.read() + '\n'
            return total
        else:
            with path.open() as f:
                return f.read()

def get_paths(paths):
    all_paths = []
    for path in paths:
        if path.is_dir():
            for p in path.glob('*.yaml'):
                all_paths.append(str(p))
        else:
            all_paths.append(str(path))
    return all_paths

def dump_str(yaml_dict):
    yaml = YAML(typ='safe')
    yaml.version = (1, 2)
    yaml.default_flow_style = False
    stream = StringIO()
    yaml.dump(yaml_dict, stream)
    return stream.getvalue()

def show_config(*paths):
    print(load_config_str(*paths))

def load_widget_config(*paths, title=''):
    widget = YamlWidgets(load_config_str(*paths), title=title)
    widget.display()
    return widget

def run_timeloop_model(*paths):
    yaml_str = dump_str(load_config(*paths))
    model = ModelApp(yaml_str, '.')
    result = model.run_subprocess()
    return result

def run_accelergy(*paths):
    has_str = False
    for path in paths:
        if isinstance(path, str):
            has_str = True
            break
    if has_str:
        yaml_str = dump_str(load_config(*paths))
        with open('tmp-accelergy.yaml', 'w') as f:
            f.write(yaml_str)
        result = invoke_accelergy(['tmp-accelergy.yaml'], '', '.')
        os.remove('tmp-accelergy.yaml')
    else:
        result = invoke_accelergy(get_paths(paths), '', '.')
    return result

def configure_mapping(config_str, mapping, var):
    config = load_config(config_str)
    for key in var:
        for level in config['options']:
            for level_key in level:
                if key == level_key:
                    var[key] = level[level_key]
    with open(mapping, 'r') as f:
        complete_mapping = eval(f.read())
    return complete_mapping

def run_timeloop_mapper(*paths):
    yaml_str = dump_str(load_config(*paths))
    mapper = MapperApp(yaml_str, '.')
    result = mapper.run_subprocess()
    return result
