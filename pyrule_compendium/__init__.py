from http.client import HTTPMessage
from typing import Union
from . import objects
from . import exceptions
from .utils import *

class compendium(object):
    """
    Base class for pyrule compendium.

    Parameters:
        * `base_url`: The base URL for the API.
            - default: "https://botw-compendium.herokuapp.com/api/v2"
            - type: string
            - notes: Manipulate with `compendium.api.base_url`
        * `default_timeout`: Default seconds to wait for response for all API calling functions until raising `requests.exceptions.ReadTimeout`
            - default: `None` (no timeout)
            - type: integer, float, tuple (for connect and read timeouts)
            - notes: If an API calling function has a parameter `timeout`, it will override this
    """

    def __init__(self, base_url: str="https://botw-compendium.herokuapp.com/api/v2", default_timeout: Union[int, float, None]=None, master_mode: bool=False):
        self.api: api = api(base_url)
        self.default_timeout = default_timeout
        self.master_mode = master_mode
        if self.master_mode: self.master_api: api = api("https://botw-compendium.herokuapp.com/api/v2/master_mode")

    def get_entry(self, entry: types.entry, timeout: types.timeout=None, master_mode: Union[bool, None]=None) -> dict:
        """
        Gets an entry from the compendium.

        Parameters:
            * `entry`: The entry to be retrieved.
                - type: str, int
            * `timeout`: Seconds to wait for response until raising `requests.exceptions.ReadTimeout`
                - default: `compendium.default_timeout`
                - type: int, float, tuple (for connect and read timeouts)
            *  `master_mode`: Specifies whether an entry is from master mode or not
                - default: None
                - type: bool, None

        Returns: Metadata on the entry
            - type: dict
        """

        if not timeout:
            timeout = self.default_timeout

        if master_mode == None:
            res: dict = self.api.request(f"/entry/{entry}", timeout)
            if not res and self.master_mode:
                res = self.master_api.request(f"/entry/{entry}", timeout)
                if res:
                    return res
                else:
                    raise exceptions.NoEntryError(entry)
            if res:
                return res
            else:
                raise exceptions.NoEntryError(entry)

        elif master_mode is True:
            res = self.master_api.request(f"/entry/{entry}", timeout)
            if res:
                return res
            else:
                raise exceptions.NoEntryError(entry)

        elif master_mode is False:
            res: dict = self.api.request(f"/entry/{entry}", timeout)
            if res:
                return res
            else:
                raise exceptions.NoEntryError(entry)

    def get_category(self, category: str, timeout: types.timeout=None, master_mode: Union[bool, None]=None) -> Union[dict, list]:
        """
        Gets all entries from a category in the compendium.

        Parameters:
            * `category`: The name of the category to be retrieved. Must be one of the compendium categories.
                - type: string
                - notes: must be in ["creatures", "equipment", "materials", "monsters", "treasure"]
            * `timeout`: Seconds to wait for response until raising `requests.exceptions.ReadTimeout`
                - default: `compendium.default_timeout`
                - type: integer, float, tuple (for connect and read timeouts)
            *  `master_mode`: Controls whether metadata is exclusively returned from the master mode endpoint or not
                - default: None
                - type: bool, None

        Returns: All entries in the category. 
            - type: list, dict (for creatures)
            - notes: the response schema of `creatures` is different from the others, as it has two sub categories: food and non_food
        """

        if not timeout:
            timeout = self.default_timeout

        if category not in ["creatures", "equipment", "materials", "monsters", "treasure"]:
            raise exceptions.NoCategoryError(category)

        if self.master_mode and category == "monsters":
            if master_mode is True: return api_req(self.master_api.base_url, timeout)
            elif master_mode is False: return self.api.request("/category/monsters", timeout)
            else: return self.api.request("/category/monsters", timeout) + api_req(self.master_api.base_url, timeout)
        else:
            if not master_mode: return self.api.request(f"/category/{category}", timeout)

    def get_all(self, timeout: types.timeout=None, master_mode: Union[bool, None]=None) -> Union[dict, list]:
        """
        Get all entries from the compendium.

        Parameters:
            * `timeout`: Seconds to wait for response until raising `requests.exceptions.ReadTimeout`
                - default: `compendium.default_timeout`
                - type: integer, float, tuple (for connect and read timeouts)
            *  `master_mode`: Controls whether metadata is exclusively returned from the master mode endpoint or not
                - default: None
                - type: bool, None

        Returns: all items in the compendium with their metadata nested in categories.
            - type: dict
        """

        if not timeout:
            timeout = self.default_timeout

        if self.master_mode and master_mode is None:
            res: dict = api_req(self.api.base_url, timeout)
            res["monsters"] += api_req(self.master_api.base_url, timeout)
            return res
        elif master_mode is True:
            return api_req(self.master_api.base_url, timeout)
        elif master_mode is False or not self.master_mode:
            return api_req(self.api.base_url, timeout)

    def get_image(self, entry: types.entry, timeout: types.timeout=None, master_mode: Union[bool, None]=None) -> objects.entry_image:
        """
        Retrieves the image of a compendium entry.

        Parameters:
            * `entry`: The ID or name of the entry.
                - type: str, int
            * `timeout`: Seconds to wait for response until raising `requests.exceptions.ReadTimeout`
                - default: `compendium.default_timeout`
                - type: integer, float, tuple (for connect and read timeouts)
            *  `master_mode`: Specifies whether an entry is from master mode or not
                - default: None
                - type: bool, None

        Returns: Entry image object
            - type: `objects.entry_image`
        """

        if not timeout:
            timeout = self.default_timeout

        if master_mode is None:
            if self._is_master_mode_entry(entry): return objects.entry_image(self.get_entry(entry, timeout=timeout, master_mode=master_mode), self.master_api)
            else: return objects.entry_image(self.get_entry(entry, timeout=timeout, master_mode=master_mode), self.api)
        if master_mode is True:
            return objects.entry_image(self.get_entry(entry, timeout=timeout, master_mode=master_mode), self.master_api)
        if master_mode is False:
            return objects.entry_image(self.get_entry(entry, timeout=timeout, master_mode=master_mode), self.api)

    def _is_master_mode_entry(self, entry: types.entry, timeout: types.timeout=None) -> bool:
        """
        Determines if an entry is from master mode or not.

        Parameters:
            * `entry`: The ID or name of the entry.
                - type: str, int
            * `timeout`: Seconds to wait for response until raising `requests.exceptions.ReadTimeout`
                - default: `compendium.default_timeout`
                - type: int, float, tuple (for connect and read timeouts)

        Returns: Whether an entry is from master mode or not
            - type: bool
        """

        if not timeout:
            timeout = self.default_timeout

        res: dict = self.api.request(f"/entry/{entry}", timeout)
        if res: return False

        res = self.master_api.request(f"/entry/{entry}", timeout)
        if res: return True

        else: raise exceptions.NoEntryError(entry)
