from crypto.blockchain.xrp import XRPService
svc = XRPService(network=testnet)
txs = svc.get_transactions(rpYqyGc8mmuFtxK1a5GuwV15ounVRvGHoT)
print(txs)
