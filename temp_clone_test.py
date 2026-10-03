from pathlib import Path
from tempfile import gettempdir
from ingestion.cloner import RepositoryCloner

url = 'https://github.com/Efeckc17/simple-example-projects-in-Python?utm_source=chatgpt.com'
cloner = RepositoryCloner(gettempdir())
print('clone_base_dir default:', gettempdir())
print('normalized url:', cloner._normalize_repo_url(url))
print('repo id:', cloner.repo_id_from_url(url))
repo_dir = cloner.clone(url, cloner.repo_id_from_url(url))
print('cloned to:', repo_dir)
print('exists:', Path(repo_dir).exists())
