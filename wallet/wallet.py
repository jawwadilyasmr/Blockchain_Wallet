import os
import subprocess
import json
from web3 import Web3
from dotenv import load_dotenv
from eth_account import Account
from bit import PrivateKeyTestnet
from bit.network import NetworkAPI
from constants import *
from web3.middleware import geth_poa_middleware
from web3.gas_strategies.time_based import medium_gas_price_strategy

load_dotenv()
private_key = os.getenv("PRIVATE_KEY")
mnemonic = os.getenv("MNEMONIC")
ETH_key = os.getenv("ETH_KEY")
BTC_key = os.getenv("BTC_KEY")
BTC = 'btc'
ETH = 'eth'
BTCTEST = 'btc-test'


w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
w3.eth.setGasPriceStrategy(medium_gas_price_strategy)
address = Web3.toChecksumAddress('0x598607fda464947507b187639389a1b47df602c0')
address2 = Web3.toChecksumAddress('0x8d597BC91A4D596663FB393Ec65fD61C1B8637a0')
w3.eth.getBalance(address)

# Use the subprocess library to call the ./derive script from Python.
def derive_wallets(coin,numderive, mnemonic):
    command = f'./derive -g --mnemonic="{mnemonic}" --format=json --coin="{coin}" --numderive="{numderive}"'
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, err = p.communicate()
    p_status = p.wait()
    keys = json.loads(output)
    return keys

#Setting dictionary of coins to be used in the wallet
coins = {"eth":derive_wallets("eth",3,mnemonic),
         "btc-test":derive_wallets("btc-test",3,mnemonic), 
         "btc":derive_wallets("btc",3,mnemonic)}
print(json.dumps(coins, indent=1))

# get the private key
eth_PrivateKey = coins[ETH][0]['privkey']
btc_PrivateKey = coins[BTC][0]['privkey']
btc_test_PrivateKey = coins[BTCTEST][0]['privkey']

# Convert the privkey string in a child key to an account object
def priv_key_to_account(coin,priv_key):
    if coin==ETH:
        return Account.from_key(priv_key)   
    elif coin==BTCTEST:
        return PrivateKeyTestnet(priv_key) 


priv_key_to_account(ETH,eth_PrivateKey)
priv_key_to_account(BTCTEST, btc_test_PrivateKey) 

# Create the raw, unsigned transaction that contains all metadata needed to transact
def create_tx(coin,account, recipient, amount):
    if coin == ETH: 
        gasEstimate = w3.eth.estimateGas(
            {"from":eth_acc.address, "to":recipient, "value": amount}
        )
        return { 
            "from": eth_acc.address,
            "to": recipient,
            "value": amount,
            "gasPrice": w3.eth.gasPrice,
            "gas": gasEstimate,
            "nonce": w3.eth.getTransactionCount(eth_acc.address),
            "chainId":11039
        }
    elif coin == BTCTEST:
        return PrivateKeyTestnet.prepare_transaction(account.address, [(recipient, amount, BTC)])

    
eth_acc = priv_key_to_account(ETH, derive_wallets(ETH,5,mnemonic)[0]['privkey'])

# create a function to send txn
def send_txn(coin,account,recipient, amount):
    txn = create_tx(coin, account, recipient, amount)
    if coin == ETH:
        signed_txn = eth_acc.sign_transaction(txn)
        result = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        print(result.hex())
        return result.hex()
    elif coin == BTCTEST:
        tx_btctest = create_tx(coin, account, recipient, amount)
        signed_txn = account.sign_transaction(txn)
        print(signed_txn)
        
        return NetworkAPI.broadcast_tx_testnet(signed_txn)
    
eth_PrivateKey = coins[ETH][0]['privkey']
btc_PrivateKey = coins[BTC][0]['privkey']
btc_test_PrivateKey = coins[BTCTEST][0]['privkey']
btc_test_acc = priv_key_to_account(BTCTEST,btc_test_PrivateKey)

# create BTCTEST transaction
create_tx(BTCTEST,btc_test_acc,"n1u1MQ11bBZvj6JzjzJKxiT5PgCsfc3ZiQ", 0.01)

# Send BTCTEST transaction
send_txn(BTCTEST,btc_test_acc,"n1u1MQ11bBZvj6JzjzJKxiT5PgCsfc3ZiQ", 0.01)

# create ETH transaction
create_tx(ETH,eth_acc,"0x8d597BC91A4D596663FB393Ec65fD61C1B8637a0", 1000)
# Send ETH transaction
send_txn(ETH, eth_acc,"0x8d597BC91A4D596663FB393Ec65fD61C1B8637a0", 1000)

