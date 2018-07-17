#!/usr/bin/env python3

import connexion

from swagger_server import encoder

from beacon_controller import utils

def main():
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'Translator Knowledge Beacon API'})

    port_config = utils.load_config(silent=False)['server']['port']
    app.run(port=port_config)

    utils.initiate_metadata_cache()


if __name__ == '__main__':
    main()
