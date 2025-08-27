from datetime import datetime
from enum import Enum
from typing import Any
import colorama, os, requests, sys

#Local import
from LichessAPI.LichessAPI import LichessApi 
from Toolkit.Toolkit import Toolkit

#Shortcut For typing
Response = requests.models.Response
Session = requests.sessions.Session

colorama.init(autoreset=True)

class Style(Enum):
    INFORMATION = ''
    SUCCESS     = colorama.Fore.GREEN
    WARNING     = colorama.Fore.YELLOW
    ERROR       = colorama.Fore.RED

class Prompt():
    """
    Class in charge of the ouput and formating strings of the CLI
    All of this output tasks are deported here for readabilty' sake
    """
    __default_style: Style
    _user_info: dict[str, Any]
    __logo: str
    _default_prompt: str

    def __init__(self, user_info: dict[str, Any]) -> None:
        self.__default_style = Style.INFORMATION
        self._user_info = user_info
        self._default_prompt = f'{user_info['username']}@lichess.org > '

        self.__logo = """
 _     _      _                     _____  _     _____ 
| |   (_)    | |                   /  __ \\| |   |_   _|
| |    _  ___| |__   ___  ___ ___  | /  \\/| |     | |  
| |   | |/ __| '_ \\ / _ \\/ __/ __| | |    | |     | |  
| |___| | (__| | | |  __/\\__ \\__ \\ | \\__/\\| |_____| |_ 
\\_____/_|\\___|_| |_|\\___||___/___/  \\____/\\_____/\\___/                                            
"""

    def bold(self, input_str: str) -> str:
        return colorama.Style.BRIGHT + input_str + colorama.Style.NORMAL

    def output(self, message: str, style: Style|None=None) -> None:
        """
        Basic method that colorizes a string based on the style passed as argument
        """

        if not isinstance(style, Style):
            style = self.__default_style

        print(f'{style.value}{message}')

    def show_welcome(self) -> None:
        """
        Shows a little message when the program is opened
        """

        message: str = f"""{self.__logo}
Welcome to the lichess CLI
You are now logged as {self.bold(self._user_info['username'])}
"""
        self.output(message)

    def show_bye(self) -> None:
        """
        Shows a little message when the program is closed
        """
        message: str = f'{os.linesep}Closing HTTP session, Bye.'
        self.output(message=message)
    
    def format_user(self, user_info: dict[str, Any]) -> str:
        """
        Formats the user command output based on the user info passed in argument
        """
        username:str        = user_info.get('username', '')
        perfs:dict[str, Any]= user_info.get('perfs', {})
        created_at: float   = user_info.get('createdAt', 0)
        seen_at:float       = user_info.get('seenAt', 0)

        is_disabled:bool     = user_info.get('disabled', False)
        acc_status = 'disabled' if is_disabled else 'enabled'

        if created_at != 0:
            created_at_formated = datetime.fromtimestamp((created_at / 1000)).strftime('[%d/%m/%Y-%H:%M:%S]')
        else:
            created_at_formated = 'N/A'
        
        if seen_at:
            seen_at_formated = datetime.fromtimestamp(seen_at / 1000).strftime('[%d/%m/%Y-%H:%M:%S]')
        else:
            seen_at_formated = 'N/A'
    
        formated_output     = f'Username: {self.bold(username)}{os.linesep}'
        formated_output    += f'Account status: {self.bold(acc_status)}{os.linesep}'
        formated_output    += f'Account Created at : {self.bold(created_at_formated)} || Last online {self.bold(seen_at_formated)}{os.linesep}'
        formated_output    += f'ELO RECAP {os.linesep * 2}'

        for perf_type, perf_info in perfs.items():
                rating: str = perf_info.get('rating','0')
                formated_output += f'{self.bold(f'\t{perf_type}')} : {rating}{os.linesep}'

        
        return formated_output
    
    def format_help(self, commands_info: dict[str, Any], command_prefix: str) -> str:
        """
        Formats the help command based on the command dict (key=command_name, value=description) and
        the command prefix 
        """
        output: str = ''
        for command_name, command_desc in commands_info.items():
            command_desc = command_desc.replace('[COMMAND_PREFIX]',command_prefix)
            output += f"{colorama.Style.BRIGHT}{command_name}{colorama.Style.NORMAL}{os.linesep}{command_desc}{os.linesep}"
        
        return output
        
class LichessCli:
    """
    Main class of the project, based on the config file
    """
    __config: dict[str,Any]
    _api_wrapper: LichessApi
    __commands: dict[str, Any]
    __command_prefix: str

    def __init__(self,config_file: str) -> None:
        self.__config               = Toolkit.get_config(config_file)
        self.__command_prefix       = self.__config['COMMAND_PREFIX']
        self.__commands             = self.__config['SUPPORTED_COMMANDS']
        self.__prefixed_commands    = [self.__command_prefix+command for command in self.__commands]
        self._api_wrapper          = LichessApi(token=self.__config['TOKEN'],
                                                baseurl=self.__config['BASE_URL'])
        
        self.__userinfo             = self._api_wrapper.get_my_profile()
        self.__prompt               = Prompt(self.__userinfo.data)

        self.__prompt.show_welcome()


    def __args_check(self, args: list[str], arg_count: int) -> bool:
        """
        Checks the if the args count fits the value specified in argument
        """
        retval = False
        if len(args) == arg_count:
            retval = True
        elif len(args) < arg_count:
            self.__prompt.output(message=f'At least {arg_count} arguments are expected!', style=Style.WARNING)
        elif len(args) > arg_count:
            self.__prompt.output(message=f'You provided too many arguments. {arg_count} arguments are expected!', style=Style.WARNING)
        
        return retval

    def __command_handler(self, user_input: str) -> None:
        """
        this method is the core of the CLI, it takes as argument the user inputs (the commands & args) and
        checks if the input is in the supported command list. It executes the method of the CLI instance
        based of a simple quick and dirty getattr() trick. 
        
        IMPORTANT: The supported commands in the config file MUST MATCH the methods names
        """

        user_command: str = user_input.split(' ')[0]
        command_args: tuple[str, ...] = tuple(user_input.split(' ')[1:])

        if user_command not in self.__prefixed_commands:
            self.__prompt.output(message=f'Unknown command! {user_command}',style=Style.ERROR)
            self.__prompt.output(message=f'type {self.__command_prefix}help to have the list of supported commands')
        else:
            method = user_command.replace(self.__command_prefix, '')
            getattr(self, f'{method}')(command_args)

    def user(self, command_args:list[str] ) -> None:
        """
        This method prints the lichess user account basic info of the specified user passed in argument
        """
        expected_args_count: int = 1

        if self.__args_check(command_args, arg_count=expected_args_count):
            username = command_args[0]
            userinfo = self._api_wrapper.get_user_info(username)
            if(not userinfo.error):
                formated_message = self.__prompt.format_user(userinfo.data)
                self.__prompt.output(formated_message, style=Style.SUCCESS)
            else:
                self.__prompt.output(f'User {username} not found', style=Style.WARNING)
    
    def quit(self, command_args:list[str]|None=None) -> None:
        """
        This method is used to gracefully close the CLI and the wrapper
        Input args : No
        """

        self._api_wrapper.close_session()
        self.__prompt.show_bye()
        sys.exit()
    
    def help(self, command_args:list[str] ) -> None:
        """
        Prints the supported commands and their usage string 
        Input args : No
        """

        output = self.__prompt.format_help(self.__commands, self.__command_prefix)
        self.__prompt.output(message=output, style=Style.WARNING)
    
    def whoami(self, command_args:list[str]|None=None) -> None:
        """
        returns the username of the account that issued the token used to connect to the lichess API
        Input args : No
        """

        output = self.__userinfo.data['username']
        self.__prompt.output(output, style=Style.SUCCESS)

    def message(self, command_args:list[str]) -> None:
        """
        sends a message to the given user
        """
        expected_args_count: int = 1

        if self.__args_check(args=command_args,arg_count=expected_args_count):
            username = command_args[0]
            message = input('Message> ')

            response = self._api_wrapper.send_message(username=username, message=message)
            if response.error:
                    self.__prompt.output(message=f'An error occured while sending the message : {response.error_message}', style=Style.ERROR)
            else:
                self.__prompt.output(message='Message sent !', style=Style.SUCCESS)

    def main(self) -> None:
        try:
            while True:
                self.__command_handler(input(self.__prompt._default_prompt))
        except KeyboardInterrupt:
            self.quit()
        except Exception as e:
            raise e

if __name__ == '__main__':
    try:
        cli = LichessCli(config_file='./Config/config.json')
        cli.main()
    except Exception as e:
        print(f'{e}')
        try:
            print('Trying to close the HTTP session is it exists')
            if isinstance(cli._api_wrapper._session, Session):
                cli._api_wrapper.close_session()
                print('HTTP Session closed')
        except Exception as e:
            print(f'Unable to close the Session: {e}')
    finally:
        print('Closing process. Bye')
        sys.exit()