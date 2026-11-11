from pathlib import Path

from oxy.utils import setting
from oxy.utils.lang.path import project_path


@project_path(parent_level=0)
def project_root() -> Path:
    pass

def project_resources():
    return project_root().joinpath('resources')

@setting.config(config_dir=project_resources(), file_name='settings.yaml')
def project_settings() -> dict:
    pass
