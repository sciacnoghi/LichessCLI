from typing import Any
import json, os

class Toolkit():
    """
    Utility class that should only contain static methods  
    """
    @staticmethod
    def check_args(inputDict: dict[str,str], mandatoryArgs: tuple[str,...]) -> None:
        missingArgList: list[str] = []
        for arg in mandatoryArgs:
            if arg not in inputDict:
                missingArgList.append(arg)

        if len(missingArgList):
            raise Exception(f'Missing args: {missingArgList}')
        
    @staticmethod
    def get_config(filename: str) -> dict[str, Any]:
        """Utility"""
        if not os.path.isfile(filename):
            raise Exception(f'Unable to locate the config file {filename}')
        
        with open(filename, mode='r', encoding='utf-8') as configFile:
            try:
                configParams = json.load(configFile)
            except Exception as e:
                raise e

        config: dict[str, Any] = {}
        for paramName, paramValue  in configParams.items():
            config.update({paramName:paramValue})

        return config


if __name__ == '__main__':
    print('This file must be imported')