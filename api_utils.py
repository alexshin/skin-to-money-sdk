from collections import OrderedDict
import hashlib
import requests
import json


class STMSignature:

    def __init__(self, salt, ignore_unsupported_values=False):
        if isinstance(salt, bytes):
            raise ValueError('Salt should be a string')

        self.salt = salt
        self.ignore_unsupported_values = ignore_unsupported_values
        self.ignore_level_deeper_than = 2

    def assemble(self, **kwargs):
        if len(kwargs) < 1:
            raise ValueError('Count of named arguments should be great than 0')
        string = self.parse_dict(kwargs, level=1)
        formatted_str = '{data};{salt}'.format(data=string, salt=self.salt)
        signed = hashlib.sha1(formatted_str.encode('utf-8')).hexdigest()
        return string, signed

    @staticmethod
    def list_to_dict(list_value):
        n = 0
        dic = {}
        for item in list_value:
            dic[str(n)] = item
            n = n + 1
        return dic

    @staticmethod
    def is_number(value):
        try:
            float(value)
        except ValueError:
            return False
        return True

    @staticmethod
    def sort_dict(dic):
        res = OrderedDict()
        for key in sorted(dic.keys()):
            res[key] = dic[key]
        return res

    def parse_dict(self, params, level=1):
        if level > self.ignore_level_deeper_than:
            return ''

        params = self.sort_dict(params)
        params.pop('signature', None)

        params_to_sign = []

        for key, value in params.items():
            if isinstance(value, bool):
                value_to_add = '1' if value else '0'
            elif isinstance(value, dict):
                value_to_add = self.parse_dict(params=value, level=level+1)
            elif isinstance(value, list):
                value_to_add = self.parse_dict(params=self.list_to_dict(value), level=level+1)
            elif value is None:
                value_to_add = ''
            elif self.is_number(value):
                value_to_add = str(value)
            elif isinstance(value, bytes):
                value_to_add = str(value)
            elif isinstance(value, str):
                value_to_add = value
            else:
                if self.ignore_unsupported_values:
                    continue
                raise ValueError(
                    'Type of value key "{key}" is not supported. '
                    'Supported types are: bool, dict, list, number'.format(key=key)
                )

            if value_to_add == '':
                continue

            params_to_sign.append('{0}:{1}'.format(str(key), value_to_add))

        return ';'.join(params_to_sign)


class STMResponse:

    ERROR_CODES = {
        203: 'Wrong signature',
        205: 'User is not found',
        404: 'Transaction is not found',
        304: 'Required argument is not found'
    }

    def __init__(self, data):
        self.data = data

    @property
    def is_error(self):
        return 'error' in self.data

    @property
    def error(self):
        if not self.is_error:
            return {}
        return {
            'code': self.data['error'],
            'message': self.ERROR_CODES.get(self.data['error'], ''),
            'original_message': self.data.get('message', '')
        }

    def get(self):
        return self.data


class STMApi:

    AVAILABLE_ACTIONS = ('create', 'info', 'marketListItems', 'marketBuyItem', 'marketWithdrawInfo', 'marketHistory')
    AVAILABLE_GAME_ID = (570, 730)

    def __init__(self, salt, url, partner_id):
        self.salt = salt
        self.url = url
        self.partner_id = partner_id
        self.sign_maker = STMSignature(self.salt)

    @staticmethod
    def _check_keys_in_the_list(keys, dic):
        return

    def _build_request_data(self, action, payload=None):
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            ValueError('Payload must be a dict')
        if action not in self.AVAILABLE_ACTIONS:
            ValueError('Action must be one from: {actions}'.format(actions=', '.join(self.AVAILABLE_ACTIONS)))
        if 'appid' in payload and payload['appid'] not in self.AVAILABLE_GAME_ID:
            ValueError('Application with id={appid} is not supported'.format(appid=payload['appid']))

        data = payload.copy()
        data['action'] = action
        data['partnerid'] = self.partner_id
        _, sign = self.sign_maker.assemble(**data)

        data['signature'] = sign

        return data

    def do_request(self, action, payload=None):
        data = self._build_request_data(action=action, payload=payload)
        response_data = requests.post(self.url, data=data)
        stm_response = STMResponse(json.loads(response_data.text))
        return stm_response

    def _do_request_with_args(self, action, args=None, **kwargs):
        args = [] if args is None else args
        if not all(name in args for name in kwargs):
            ValueError('There is/are not required args. Required args: {0}'.format(', '.join(args)))
        return self.do_request(action=action, payload=kwargs)

    def get_market_list_items(self, **kwargs):
        return self._do_request_with_args('marketListItems', args=['appid'], **kwargs)

    def do_market_buy_item(self, **kwargs):
        args = ['id', 'price', 'currency', 'trade_link']
        return self._do_request_with_args('marketBuyItem', args, **kwargs)

    def get_market_withdraw_info(self, **kwargs):
        return self._do_request_with_args('marketWithdrawInfo', args=['id_withdraw'], **kwargs)

    def get_market_history(self, **kwargs):
        return self._do_request_with_args('marketHistory', args=[], **kwargs)

    def create_order(self, **kwargs):
        if 'sandbox' not in kwargs:
            kwargs['sandbox'] = True
        args = ['amount', 'successUrl', 'failUrl', 'sandbox']
        return self._do_request_with_args('create', args=args, **kwargs)

    def get_order_info(self, **kwargs):
        return self._do_request_with_args('info', args=['idtr'], **kwargs)
