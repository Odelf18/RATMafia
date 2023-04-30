from web3 import Web3
import json, sys, datetime
from style import style, text

with open("config.json") as f:
    keys = json.load(f)

class bot():
    def __init__(self):
        print("\nApprove contract")
        self.router_address = "0xc873fEcbd354f5A56E00E710B90EF4201db2448d"
        self.factory_address = "0x27A6cf5E8350b44273FB10F98D78525c5DAD6d8a"
        self.max_uint256 = 115792089237316195423570985008687907853269984665640564039457584007913129639935

        self.w3 = self.connect()
        self.address, self.private_key = self.setup_address()
        self.token_contract = self.setup_token()
        self.approve()

    def connect(self):
        w3 = Web3(Web3.HTTPProvider(keys["HTTPProvider"]))
        if(w3.is_connected):
            print(text.GREEN + "Script successfully connected to the node !" + style.RESET)
        else:
            print(text.RED + "Script failed to connect to node, please fix the issue." + style.RESET)
        return w3

    def setup_address(self):
        wallet_address = self.w3.to_checksum_address(keys["metamask_address"])
        return wallet_address, keys["metamask_private_key"]

    def setup_token(self):
        with open("./ABIs/erc20_abi.json") as f:
            contract_abi = json.load(f)

        while True:
            token_contract_address = str(input("\n{}Please enter the {}CONTRACT ADDRESS{} of the token {}(needs to be paired with WAVAX){}:{} ".format(text.WHITE, text.RED, text.WHITE, text.RED, text.WHITE, style.RESET)))

            if self.w3.is_address(token_contract_address):
                self.token_address = self.w3.to_checksum_address(token_contract_address)
                break

            else:
                print(f"\n{text.RED}Please give a correct contract address (e.g. : 0x959b88966fC5B261dF8359961357d34F4ee27b4a){style.RESET}")
                continue
        
        token_contract = self.w3.eth.contract(address=self.token_address, abi=contract_abi)
        return token_contract

    def is_approved(self):
        approved = self.token_contract.functions.allowance(self.address, self.router_address).transact()
        requiring_approve = self.token_contract.functions.balanceOf(self.address).transact()
        if int(approved) <= int(requiring_approve):
            return False
        else:
            return True

    def approve(self):
        if self.is_approved() == False:
            self.approve_nonce = self.w3.eth.get_transaction_count(self.address)

            self.checkGasPrice()
            txn = self.token_contract.functions.approve(
                self.router_address,
                self.max_uint256
                ).buildTransaction({
                    'from': self.address,
                    'gas': self.gas_limit,
                    'gasPrice': self.w3.eth.gas_price,
                    'nonce': self.approve_nonce
                })

            signed_txn = self.w3.eth.account.sign_transaction(txn, self.private_key)

            txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
            current_time = self.get_current_time()
            print(f"{text.BLUE}{current_time} | APPROVE TRANSACTION | Pending.... | Hash : {txn.hex()} {style.RESET}")

            txn_receipt = self.w3.eth.wait_for_transaction_receipt(txn)
            current_time = self.get_current_time()
            if txn_receipt['status'] == 1: 
                print(f"{text.GREEN}\n{current_time} | APPROVE TRANSACTION | Transaction successful ! | Tx : {txn.hex()}")
                print("Link to Tx : https://arbiscan.io/tx" + txn.hex() + style.RESET)
                return True
            else:
                print(f"{text.RED}\n{current_time} | APPROVE TRANSACTION | Transaction Failed ! | Tx : {txn.hex()}")
                print("Link to Tx : https://arbiscan.io/tx" + txn.hex() + style.RESET)
                return False

        else:
            current_time = self.get_current_time()
            print(f"{text.GREEN}\n{current_time} | Contract is already approved !{style.RESET}")
            return True

    def get_current_time(self):
        now = datetime.datetime.utcnow()
        return now.strftime("%H:%M:%S")
