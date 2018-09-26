#!/usr/bin/env python3

import connexion
from swagger_server import encoder
from flask import redirect
from beacon_controller import config

BASEPATH = f'/beacon/{config["beacon_name"]}/'

def handle_error(e):
    return redirect(BASEPATH)

def main():
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api(
        'swagger.yaml',
        base_path=BASEPATH,
        swagger_url='/',
        arguments={'title': 'Translator Knowledge Beacon API'}
    )
    app.add_error_handler(404, handle_error)

    app.run(port=config['port'], server='tornado')

if __name__ == '__main__':
    main()
