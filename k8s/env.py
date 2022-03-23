import os

SETTINGS_DIR = 'regions'
DEFAULT_REGION = 'oregon-b'
DEFAULT_ENV = 'dev'
TEMPLATE_DIR = os.path.join(
    os.sep,
    os.path.dirname(
        os.path.realpath(__file__)),
    'templates')

# template names
SUMO_APP_TEMPLATE = 'sumo-app.yaml.j2'
SUMO_NODEPORT_TEMPLATE = 'sumo-nodeport.yaml.j2'
SUMO_SERVICE_TEMPLATE = 'sumo-service.yaml.j2'
SUMO_HPA_TEMPLATE = 'sumo-web-hpa.yaml.j2'
