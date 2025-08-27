import requests,json, os 
from typing import Any

#Shortcut For typing
Response = requests.models.Response
Session = requests.sessions.Session

class GenericResponse():
    """
    This class is used to format into simple objects the request responses from the lichess API
        status_code     : HTTP status code
        data            : payload of the request response
        time_elapsed    : time it took for the 
        error           : error flag (bool)
        error_message   : content of the error
    """
    status_code: int
    data:dict[str, Any]
    time_elapsed: float
    error: bool
    error_message: str | None

    def __init__(self, response: Response) -> None:
        self.status_code  = response.status_code
        self.time_elapsed = response.elapsed.microseconds
        self.error = True

        if response.status_code >= 200 and response.status_code <= 299:
            self.error = False
            if response.text:
                try:
                    self.data = json.loads(response.text)
                except json.decoder.JSONDecodeError:
                    self.error_message = f'Unable to decode JSON: {os.linesep}{response.text}'
        elif response.status_code == 400:
            self.error_message = response.text if response.text else None 
        else:
            self.error_message = response.reason


class LichessApi:
    """
    API Wrapper class to interact with the lichess API
    """
    __token: str
    __baseurl: str
    __headers: dict[str,Any]
    _session: Session

    def __init__(self, token: str, baseurl: str) -> None:
        self._session   = requests.Session()
        self.__token    = token
        self.__baseurl  = baseurl
        self.__headers  = {'Authorization': 'Bearer {}'.format(self.__token),
                           'Accept': 'application/json'}


    def __send_request(self,
                        url: str, 
                        method: str,
                        data: dict[str, Any] | str | None = None,
                        additionnal_headers: dict[str, Any] | None = None,
                        params: dict[str, Any] | None = None ) -> GenericResponse:
        
        """
        The core method that stages the parameter before sending the request to the lichess API
        the response is formated according to the GenericResponse custom class

        Nota Bene: additionnal_headers have the priority over the headers set during the initialisation
        of the instance, except for Authorization, which would mess up with the auth.
        """

        headers = self.__headers
        if additionnal_headers:
            for key, item in additionnal_headers.items():
                if key != 'Authorization':
                    headers.update({key:item})

        try:
            response = self._session.request(url=url, method=method, headers=headers, data=data, params=params)
            formated_response = GenericResponse(response=response)
        except Exception as e:
            raise e

        return formated_response

    def get_user_info(self, username: str) -> GenericResponse:
        """Gets user info based on username passed as argument
        https://lichess.org/api#tag/Users/operation/apiUser
        """
        endpoint: str = f'api/user/{username}'
        return self.__send_request(url=f'{self.__baseurl}{endpoint}',
                                   method = 'get')
    
    def get_users_by_id(self, userlist: list[str]) -> GenericResponse:
        """
        gets the info of a comma separated list of username
        https://lichess.org/api#tag/Users/operation/apiUsers
        """
        users: str = ','.join(userlist)
        endpoint: str = 'api/users'
        add_headers: dict[str, str] = {'Content-Type':'text-plain'}

        return self.__send_request(url=f'{self.__baseurl}{endpoint}',
                                   method ='post',
                                   data=users,
                                   additionnal_headers=add_headers)
    
    def get_my_profile(self) -> GenericResponse:
        """
        Gets the account info the issuer of the API token
        https://lichess.org/api#tag/Account/operation/accountMe
        """
        endpoint : str = 'api/account'
        return self.__send_request(url=f'{self.__baseurl}{endpoint}',
                                   method='get')
    

    def send_message(self, username: str, message: str) -> GenericResponse:
        """
        Sends a private message to the receipient 
        https://lichess.org/api#tag/Messaging/operation/inboxUsername
        """
        endpoint: str = f'/inbox/{username}'
        add_headers: dict[str, str] = {'Content-Type':'application/x-www-form-urlencoded'}
        data = {'text':message}

        return self.__send_request(url=f'{self.__baseurl}{endpoint}',
                                   method='post',
                                   data=data,
                                   additionnal_headers=add_headers)
    
    def close_session(self) -> None:
        """
        Closes gracefully the requests session (readability purpose)
        """
        self._session.close()


if __name__ == '__main__':
    print('This file must be imported')