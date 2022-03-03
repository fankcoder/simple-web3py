import os
import json
import time
from web3 import Web3, contract
from web3.middleware import geth_poa_middleware
from web3._utils.events import get_event_data


MAIN_POINT = ""
TEST_NET_POINT = "https://rinkeby.infura.io/v3/xxxx"
MINTER_ADDRESS = ''
MINTER_PRI_KEY = ''
IS_MAIN_NET = False
project_root = '.'
MNEMONIC = ""
MNEMONIC_NUMBER = "0"


class SimpleWeb3(object):
    if IS_MAIN_NET:
        NET_POINT = MAIN_POINT
    else:
        NET_POINT = TEST_NET_POINT
    w3 = Web3(Web3.HTTPProvider(NET_POINT, request_kwargs={'timeout': 60}))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    contract_address = {}
    contract_abi = {}

    mnemonic = MNEMONIC
    mnemonic_number = MNEMONIC_NUMBER

    def __init__(self, contract_address_dict, contract_abi_dict, minter_address=None, minter_pri_key=None, mnemonic_number=None):

        for key in contract_address_dict:
            self.contract_address[key] = contract_address_dict[key]
        
        for key in contract_abi_dict:
            if IS_MAIN_NET:
                self.contract_abi[key] = os.path.join(project_root) + "/abi/contracts/" + contract_abi_dict[key]
            else:
                self.contract_abi[key] = os.path.join(project_root) + "/abi/contracts_test/" + contract_abi_dict[key]

        if minter_address:
            self.private_key = minter_pri_key
            self.miner = self.w3.toChecksumAddress(minter_address.lower())
        else:
            self.private_key = MINTER_PRI_KEY
            self.miner = self.w3.toChecksumAddress(MINTER_ADDRESS.lower())

        self.golbol_nonce = self.w3.eth.get_transaction_count(self.miner, 'pending')


    def get_prikey_with_mnemonic(self, mnemonic, number=0):
        w3 = self.w3
        w3.eth.account.enable_unaudited_hdwallet_features()
        account = web3.eth.account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/{}".format(number))
        return account.address, account.key

    def get_miner_nonce(self, count=0):
        nonce = self.w3.eth.get_transaction_count(self.miner, "pending")
        max_count = 0
        while self.golbol_nonce == nonce and max_count < 10:
            nonce = self.w3.eth.get_transaction_count(self.miner, "pending")
            max_count += 1
            time.sleep(1)
        self.golbol_nonce = nonce
        return nonce

    def get_gas_price(self):
        eth_gas_price = int(self.w3.eth.gasPrice * 1.5)
        return eth_gas_price

    def get_now_block_number(self):
        return self.w3.eth.block_number

    def get_abi(self, contract_name):
        with open(self.contract_abi[contract_name], 'r', encoding='UTF-8') as f:
            res = f.read()
            return json.loads(res)
    
    def get_contract_obj(self, contract_name):
        return self.w3.eth.contract(address=self.contract_address[contract_name], abi=self.get_abi(contract_name))

    def get_func(self, contract_name, func_name, *args):
        contract = self.get_contract_obj(contract_name)
        return getattr(contract.functions, func_name)(*args)

    def write(self, contract_name, func_name, *args):
        try:
            w3 = self.w3
            _func = self.get_func(contract_name, func_name, *args)

            nonce = self.get_miner_nonce()
            unicorn_txn = _func.buildTransaction({
                'from': self.miner,
                'chainId': w3.eth.chain_id,
                'gas': 5500000,
                'gasPrice': self.get_gas_price(),
                'nonce': nonce
            })
            signed_txn = w3.eth.account.sign_transaction(unicorn_txn, private_key=self.private_key)
            w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            sign_hash = signed_txn.hash
            txhash = sign_hash.hex()
            res = w3.eth.wait_for_transaction_receipt(txhash, timeout=60*5)
            if res.get('status', 0) == 1:
                return res
            else:
                return None
        except Exception as e:
            # with open(r'/var/log/ku/tmp_web3.log', 'a+', encoding='utf8') as ef:
            #     ef.write(f'》》》》》{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}《《《《《\n'
            #              f'{e}\n\n\n')
            print(e)
            return None
    
    def read(self, contract_name, func_name, *args):
        _func = self.get_func(contract_name, func_name, *args)
        res = _func.call({
            'from': self.miner,
        })
        return res

    def try_get_event_data(self, event, event_template):
        try:
            return get_event_data(event_template.web3.codec, event_template._get_event_abi(), event)
        except:
            return None

    def event(self, contract_name: str, from_block: int, to_block: int,
                                          event_name_list: list):
        address = self.contract_address.get(contract_name)
        contract = self.get_contract_obj(contract_name)
        result = []
        events = self.w3.eth.getLogs({'fromBlock': from_block, 'toBlock': to_block, 'address': address})
        event_templates = [contract.events[event_name] for event_name in event_name_list]
        for event in events:
            for event_template in event_templates:
                res = self.try_get_event_data(event, event_template)
                if res is not None:
                    result.append(res)
                    break
        return result

if __name__ == '__main__':
    contract_address_dict = {'ContractNameA': '0x123', 'ContractNameB':'0x123'}
    contract_abi_dict = {'ContractNameA': 'ContractNameA.json', 'ContractNameB': 'ContractNameB.json'}
    MINTER_ADDRESS = ""
    PRI_ADDRESS = ""
    s_web3 = SimpleWeb3(contract_address_dict=contract_address_dict, contract_abi_dict=contract_abi_dict,
                        minter_address=WHITELIST_MINTER_ADDRESS, minter_pri_key=WHITELIST_PRI_ADDRESS)
    # resp = s_web3.write('ContractNameA', 'transfer', '0x123', 1)

    # resp = s_web3.read('ContractNameB', 'ownerOf')

    # from_block = 10127103
    # to_block = 10127203
    # event_name_list = ["Transfer"]

    # resp = s_web3.event('ContractNameA', from_block, to_block, event_name_list)
    # print(resp)