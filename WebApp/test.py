from Automation.BDaq.InstantAiCtrl import InstantAiCtrl
from Automation.BDaq.InstantAoCtrl import InstantAoCtrl
from Automation.BDaq.BDaqApi import ErrorCode

print("Initializing...")
ai = InstantAiCtrl("USB-4716,BID#0")
ao = InstantAoCtrl("USB-4716,BID#0")

print("Reading AI...")
err, data = ai.readDataF64(0, 2)
print("Error:", err)
print("Data:", data)

print("Writing AO...")
err = ao.writeAny(0, 1, None, [2.5])
print("Error:", err)
