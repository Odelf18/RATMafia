import json, sys, tj_snipe_manually, tj_snipe_telegram, tj_snipe_liquidity, tj_approve
from style import style, text

header = """
----------------------------------------------------
    ____  ___  ______   __  ______    _____________ 
   / __ \/   |/_  __/  /  |/  /   |  / ____/  _/   |
  / /_/ / /| | / /    / /|_/ / /| | / /_   / // /| |
 / _, _/ ___ |/ /    / /  / / ___ |/ __/ _/ // ___ |
/_/ |_/_/  |_/_/    /_/  /_/_/  |_/_/   /___/_/  |_|
                                                    
                      v0.1.0
            Sniper Bot created by @0xKzz_                 
----------------------------------------------------
"""

class sniperConfig():
    def __init__(self):
        self.verifyJSON()
        self.configMode()
        self.startBot()

    def verifyJSON(self):
        with open("config.json") as f:
            keys = json.load(f)
        
        keywords = ["amount_in", "slippage", "gas_price_superfast", "gas_price_fast", "gas_price_normal", "gas_limit"]

        for eachKeyword in keywords:
            if keys[eachKeyword] < 0:
                print(text.RED + "Please configure the config.json file " + eachKeyword + " must be greater than 0." + style.RESET)
                sys.exit()

        if len(keys["metamask_address"]) <= 41:
            print(text.RED +"Please configure your Address in the config.json file! Exiting script.." + style.RESET)
            sys.exit()

        if len(keys["metamask_private_key"]) <= 42:
            print(text.RED +"Please configure your PrivateKey in the config.json file! Exiting script.."+ style.RESET)
            sys.exit()

        print(text.GREEN +"File config.json has been verified! Starting script.."+ style.RESET)
    
    def configMode(self):
        print("\n" + text.YELLOW + "-" * 100 + style.RESET)
        print(f"\n{style.ITALIC}What action do you want to do?{style.RESET}")
        print(f"\n  [1] Snipe Token Stealth Launch (Manually)")
        print(f"  [2] Snipe Token Stealth Launch (Telegram Scrapper)")
        print(f"  [3] Snipe Liquidity")
        print(f"  [4] Approve contract")

        while True :
            inputChoice = int(input("{}{}Please enter your choice :{} ".format(text.YELLOW, style.UNDERLINE, style.RESET)))

            if inputChoice == 1:
                self.mode = 1
                break
            elif inputChoice == 2:
                self.mode = 2
                break
            elif inputChoice == 3:
                self.mode = 3
                break
            elif inputChoice == 4:
                self.mode = 4
                break
            else:
                print(f"{text.RED}Please enter a valid mode.{style.RESET}")
                continue

        print("\n" + text.YELLOW + "-" * 100 + style.RESET)

    def startBot(self):
        if(self.mode == 1):
            bot = tj_snipe_manually.bot()
            if bot.buyToken():   
                if bot.approve():
                    if bot.amount_to_sell():
                        print("\n" + text.YELLOW + "=" * 50)
                        print("End of the script.")
                        print("\n" + "=" * 50 + style.RESET)
                        sys.exit()

        if(self.mode == 2):
            bot = tj_snipe_telegram.bot()
            if bot.buyToken():   
                if bot.approve():
                    if bot.amount_to_sell():
                        print("\n" + text.YELLOW + "=" * 50)
                        print("End of the script.")
                        print("\n" + "=" * 50 + style.RESET)
                        sys.exit()

        if(self.mode == 3):
            bot = tj_snipe_liquidity.bot()

        if(self.mode == 4):
            bot = tj_approve.bot()


################################################ MAIN ################################################

#Print the welcome message, only once.
print(text.YELLOW + header + style.RESET)
sniperConfig()
