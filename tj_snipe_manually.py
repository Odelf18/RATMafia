from web3 import Web3
import json, sys, time, datetime, threading
from pynput import keyboard 
from style import style, text

with open("config.json") as f:
    keys = json.load(f)

class bot():
    def __init__(self):
        self.wavax_address = "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7"
        self.router_address = "0x60aE616a2155Ee3d9A68541Ba4544862310933d4"
        self.factory_address = "0x9Ad6C38BE94206cA50bb0d90783181662f0Cfa10"
        self.max_uint256 = 115792089237316195423570985008687907853269984665640564039457584007913129639935

        print("\nSnipe manually mode")
        self.w3 = self.connect()
        self.address, self.private_key = self.setup_address()
        self.buy_amount = self.setup_buy()
        self.router_contract = self.setup_router()
        self.slippage = self.setup_slippage()
        self.setup_gas_fees()
        self.token_contract = self.setup_token()
        self.path_buying, self.path_selling = self.setup_path()
        self.token_pair_contract = self.setup_token_pair()
        self.token_name, self.token_symbol = self.setup_token_informations()
        self.txn_recap()

    def connect(self):
        w3 = Web3(Web3.HTTPProvider(keys["HTTPProvider"]))
        if(w3.isConnected):
            print(text.GREEN + "Script successfully connected to the node !" + style.RESET)
        else:
            print(text.RED + "Script failed to connect to node, please fix the issue." + style.RESET)
        return w3

    def setup_address(self):
        wallet_address = self.w3.toChecksumAddress(keys["metamask_address"])
        return wallet_address, keys["metamask_private_key"]

    def setup_buy(self):
        max_amount = self.w3.eth.getBalance(self.address)
        amount_in = int(self.w3.toWei(keys["amount_in"], 'ether'))
    
        if amount_in >= max_amount:
            print(f"{text.RED}\nPlease modify your amount_in value in the config.json file, not enough funds in balance [0 < amount_in < {max_amount * 10**-18} AVAX]! Exiting script..{style.RESET}")
            sys.exit()
        
        print("\n" + text.YELLOW + "Wallet :")
        print(f"{self.address}  |  Balance : {max_amount* 10**-18} AVAX  |  Amount to trade : {amount_in * 10**-18} AVAX{style.RESET}")
        return amount_in

    def setup_router(self):
        with open("./ABIs/tj_router_abi.json") as f:
            tj_router_abi = json.load(f)

        tj_router_contract = self.w3.eth.contract(address = self.router_address, abi = tj_router_abi)
        return tj_router_contract

    def setup_token_pair(self):
        with open("./ABIs/tj_factory_abi.json") as f:
            tj_factory_abi = json.load(f)

        with open("./ABIs/tj_pair_abi.json") as f:
            tj_pair_abi = json.load(f)

        factory_contract = self.w3.eth.contract(address = self.factory_address, abi = tj_factory_abi)
        token_pair_address = factory_contract.functions.getPair(self.token_address, self.wavax_address).call()
        pair_contract = self.w3.eth.contract(address = token_pair_address, abi = tj_pair_abi)

        return pair_contract

    def setup_slippage(self):
        slippage = 100 - keys['slippage']
        slippage = slippage/100
        return slippage

    def setup_gas_fees(self):
        gas_price_superfast = int(self.w3.toWei(keys['gas_price_superfast'], 'gwei'))
        gas_price_fast = int(self.w3.toWei(keys['gas_price_fast'], 'gwei'))
        gas_price_normal = int(self.w3.toWei(keys['gas_price_normal'], 'gwei'))
        self.gas_limit = keys['gas_limit']
        print("\n" + text.YELLOW + "-" * 100 + style.RESET)
        print(f"\nChoose your gas strategy:")
        print(f"\n{text.RED}  => [1] SUPERFAST gas price{style.RESET}")
        print(f"{text.YELLOW}  => [2] FAST gas price{style.RESET}")
        print(f"{text.CYAN}  => [3] NORMAL gas price{style.RESET}")
        while True:  
            gas_strategy = int(input("\nEnter your choice: "))
            if(gas_strategy == 1):
                self.gas_price = gas_price_superfast
                break
            elif(gas_strategy == 2):
                self.gas_price = gas_price_fast
                break
            elif(gas_strategy == 3):
                self.gas_price = gas_price_normal
                break
            else:
                print(f"{text.RED}Please chose one of the strategies specified above.{style.RESET}")
                continue
        print("\n" + text.YELLOW + "-" * 100 + style.RESET)


    def setup_token(self):
        with open("./ABIs/erc20_abi.json") as f:
            contract_abi = json.load(f)

        while True:
            token_contract_address = str(input("\n{}Please enter the {}CONTRACT ADDRESS{} of the token {}(needs to be paired with WAVAX){}:{} ".format(text.WHITE, text.RED, text.WHITE, text.RED, text.WHITE, style.RESET)))

            if self.w3.isAddress(token_contract_address):
                self.token_address = self.w3.toChecksumAddress(token_contract_address)
                break

            else:
                print(f"\n{text.RED}Please give a correct contract address (e.g. : 0x959b88966fC5B261dF8359961357d34F4ee27b4a){style.RESET}")
                continue
        
        token_contract = self.w3.eth.contract(address=self.token_address, abi=contract_abi)
        return token_contract

    def setup_path(self):
        return [self.wavax_address, self.token_address], [self.token_address, self.wavax_address]

    def setup_token_informations(self):
        return self.token_contract.functions.name().call(), self.token_contract.functions.symbol().call()
    
    def get_token_balance(self): 
        return self.token_contract.functions.balanceOf(self.address).call()

    def txn_recap(self):
        print("\n" + text.YELLOW + "=" * 50 + style.RESET)
        print(f"\nContract : {self.token_address}")
        print(f"Name : {self.token_name}")
        print(f"Symbol : {self.token_symbol}")
        print("\n" + text.YELLOW + "=" * 50 + style.RESET)

    def buyToken(self):
        self.buy_nonce = self.w3.eth.get_transaction_count(self.address)
        self.checkGasPrice()
        txn = self.router_contract.functions.swapExactAVAXForTokensSupportingFeeOnTransferTokens(0, self.path_buying, self.address, int(time.time()) + 600).buildTransaction({
                'from': self.address,
                'value': self.buy_amount,
                'gasPrice': self.gas_price,
                'nonce': self.buy_nonce
            })

        signed_txn = self.w3.eth.account.sign_transaction(txn, self.private_key)

        txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        current_time = self.get_current_time()
        print(f"{text.BLUE}\n{current_time} | BUY TRANSACTION | Pending.... | Hash : {txn.hex()} {style.RESET}")

        txn_receipt = self.w3.eth.wait_for_transaction_receipt(txn)
        if txn_receipt['status'] == 1: 
            self.bought_token_price, ts = self.price_update()
            
            current_time = self.get_current_time()

            print(f"{text.GREEN}\n {current_time} | BUY TRANSACTION | Transaction successful ! | Bought : {self.get_token_balance()} {self.token_symbol} | For : {self.buy_amount * 10**-18} AVAX | Price per token : {self.bought_token_price} AVAX | Tx : {txn.hex()}")
            print("Link to Tx : https://snowtrace.io/tx/" + txn.hex() + style.RESET)
            return True
        else:
            print(f"{text.RED}\n{current_time} | BUY TRANSACTION | Transaction Failed ! | Tx : {txn.hex()}")
            print("Link to Tx : https://snowtrace.io/tx/" + txn.hex() + style.RESET)
            return False

    def is_approved(self):
        approved = self.token_contract.functions.allowance(self.address, self.router_address).call()
        requiring_approve = self.token_contract.functions.balanceOf(self.address).call()
        if int(approved) <= int(requiring_approve):
            return False
        else:
            return True

    def approve(self):
        if self.is_approved() == False:
            self.nonce_approve = self.w3.eth.get_transaction_count(self.address)
            if self.nonce_approve  == self.buy_nonce:
                self.nonce_approve = self.nonce_approve + 1

            self.checkGasPrice()
            txn = self.token_contract.functions.approve(
                self.router_address,
                self.max_uint256
                ).buildTransaction({
                    'from': self.address,
                    'gas': self.gas_limit,
                    'gasPrice': self.gas_price,
                    'nonce': self.nonce_approve
                })

            signed_txn = self.w3.eth.account.sign_transaction(txn, self.private_key)

            txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
            current_time = self.get_current_time()
            print(f"{text.BLUE}{current_time} | APPROVE TRANSACTION | Pending.... | Hash : {txn.hex()} {style.RESET}")

            txn_receipt = self.w3.eth.wait_for_transaction_receipt(txn)
            current_time = self.get_current_time()
            if txn_receipt['status'] == 1: 
                print(f"{text.GREEN}\n{current_time} | APPROVE TRANSACTION | Transaction successful ! | Tx : {txn.hex()}")
                print("Link to Tx : https://snowtrace.io/tx/" + txn.hex() + style.RESET)
                return True
            else:
                print(f"{text.RED}\n{current_time} | APPROVE TRANSACTION | Transaction Failed ! | Tx : {txn.hex()}")
                print("Link to Tx : https://snowtrace.io/tx/" + txn.hex() + style.RESET)
                return False

        else:
            current_time = self.get_current_time()
            print(f"{text.GREEN}\n{current_time} | Contract is already approved !{style.RESET}")
            return True
    
    def price_update(self):
        token_get_reserves = self.token_pair_contract.functions.getReserves().call()
        token0_address = self.token_pair_contract.functions.token0().call()
        if self.w3.toChecksumAddress(token0_address) == self.token_address:
            current_token_price = token_get_reserves[1] / token_get_reserves[0]
        else:
            current_token_price = token_get_reserves[0] / token_get_reserves[1]
        return current_token_price, int(token_get_reserves[2])

    def get_current_time(self):
        now = datetime.datetime.utcnow()
        return now.strftime("%H:%M:%S")

    def getOutputToAVAX(self, amount_sell):
        amounts_out = self.router_contract.functions.getAmountsOut(amount_sell, self.path_selling).call()
        amount_out = amounts_out[1]
        return int(amount_out * self.slippage)

    def thread_function(self):
        while self.threadLoop:
            self.current_token_price, ts = self.price_update()

            price_variation = ((self.current_token_price / self.bought_token_price) - 1)*100

            time_utc = datetime.datetime.utcfromtimestamp(ts).strftime('%H:%M:%S')

            current_time = self.get_current_time()

            if price_variation > 0: variation_text_color = text.GREEN
            elif price_variation == 0 : variation_text_color = text.BLUE
            elif price_variation < 0 : variation_text_color = text.RED

            print(f"Last Check : {current_time}  |  Last TX : {time_utc}  |  Current price : {self.current_token_price} WAVAX  |  Bought for : {self.bought_token_price} WAVAX  |  {variation_text_color}Variation : {price_variation} %{style.RESET}")
            time.sleep(0.8)
        
    def amount_to_sell(self):
        print("\nSelect one of the options below:\n")
        print(f"{text.YELLOW}[F1] Sell 25%")
        print("[F2] Sell 50%")
        print("[F3] Sell 75%")
        print(f"[F4] Sell 100%{style.RESET}\n")

        self.threadLoop = True
        threading.Thread(target=self.thread_function).start()

        with keyboard.Listener(on_press = self.on_press) as self.listener: 
            self.listener.join()

    def on_press(self, key):         
        if(key == keyboard.Key.f1):
            self.listener.stop()
            self.threadLoop = False
            self.sell_token(0.25)

        elif(key == keyboard.Key.f2):
            self.listener.stop()
            self.threadLoop = False
            self.sell_token(0.50)

        elif(key == keyboard.Key.f3):
            self.listener.stop()
            self.threadLoop = False
            self.sell_token(0.75)

        elif(key == keyboard.Key.f4):
            self.listener.stop()
            self.threadLoop = False
            self.sell_token(1)

    def sell_token(self, coef):
        amount_sell = int(self.get_token_balance() * coef)
        self.checkGasPrice()
        txn = self.router_contract.functions.swapExactTokensForAVAXSupportingFeeOnTransferTokens(
            amount_sell,
            self.getOutputToAVAX(amount_sell),
            self.path_selling,
            self.address,
            int(time.time()) + 600
            ).buildTransaction({
                'from': self.address,
                'value': 0,
                'gas': self.gas_limit,
                'gasPrice': self.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.address)
            })

        signed_txn = self.w3.eth.account.sign_transaction(txn, self.private_key)

        txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        current_time = self.get_current_time()
        print(f"{text.BLUE}{current_time} | SELL TRANSACTION | Pending.... | Hash : {txn.hex()} {style.RESET}")

        txn_receipt = self.w3.eth.wait_for_transaction_receipt(txn)
        current_time = self.get_current_time()
        if txn_receipt['status'] == 1: 
            print(f"{text.GREEN}\n{current_time} | SELL TRANSACTION | Transaction successful ! | Tx : {txn.hex()}")
            print("Link to Tx : https://snowtrace.io/tx/" + txn.hex() + style.RESET)
            return True
        else:
            print(f"{text.RED}\n{current_time} | SELL TRANSACTION | Transaction Failed ! | Tx : {txn.hex()}")
            print("Link to Tx : https://snowtrace.io/tx/" + txn.hex() + style.RESET)
            return False

    def checkGasPrice(self):
        minimum_gas_price = self.w3.eth.gas_price
        if(self.gas_price < minimum_gas_price):
            self.gas_price = int(minimum_gas_price * 1.2)
