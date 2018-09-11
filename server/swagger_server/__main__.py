#!/usr/bin/env python3

import connexion

from swagger_server import encoder

from beacon_controller import config

def main():
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'Translator Knowledge Beacon API'})

    app.run(port=config['server']['port'])

if __name__ == '__main__':
    main()
