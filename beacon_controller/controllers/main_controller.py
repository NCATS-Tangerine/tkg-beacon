import connexion

from swagger_server import encoder
from flask import redirect
from beacon_controller import config

BASEPATH = f'/beacon/{config["beacon_name"]}/'


def main(name:str):
    """
    Usage in swagger_server/main.py:

        from beacon_controller import run
        if __name__ == '__main__':
            run(__name__)
    """
    app = connexion.App(name, specification_dir='./swagger/', server=config['server'])

    app.app.json_encoder = encoder.JSONEncoder
    app.app.json_encoder.include_nulls = config['include_nulls']

    app.add_api(
        'swagger.yaml',
        base_path=BASEPATH,
        swagger_url='/',
        arguments={'title': config['title']}
    )

    if config['redirect_404'] and isinstance(BASEPATH, str):
        app.add_error_handler(404, lambda e: redirect(BASEPATH))

    app.run(port=config['port'])
