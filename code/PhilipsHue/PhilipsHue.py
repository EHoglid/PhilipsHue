#!/usr/bin/python
from phue import Bridge
import random

b = Bridge("192.168.0.80") # Enter bridge IP here.

#If running for the first time, press button on bridge and run with b.connect()
#uncommented
#b.connect()
lights = b.get_light_objects()
nofLamps = len(lights)

# --------------------------------------------------------------------------- #
# import the modbus libraries we need
# --------------------------------------------------------------------------- #
from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSparseDataBlock
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer

#---------------------------------------------------------------------------#
# configure the service logging
#---------------------------------------------------------------------------#
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.ERROR)

# --------------------------------------------------------------------------- #
# create your custom data block with callbacks
# --------------------------------------------------------------------------- #
class CallbackCoilBlock(ModbusSparseDataBlock):
    """ A datablock that stores the new value in memory
    and passes the operation to a message queue for further
    processing.
    """

    def __init__(self):

        values = {i:False for i in range(0, 2000)}
        super(CallbackCoilBlock, self).__init__(values)

    def getValues(self, address, count=1):
        values = []
        for mb_adr in range(address, (address + count)):
            value = False

            if (mb_adr == 1001):
                value = b.get_group(5)['action']['on']
            elif (mb_adr == 1010):
                value = b.get_group(0)['action']['on'] # All lamps in the bridge
            else:
                hue_adr = mb_adr - 1
                if (hue_adr < nofLamps):
                    value = bool(lights[hue_adr].on)
                    
            values.extend([value])

        super(CallbackCoilBlock, self).setValues(address, values)
        return super(CallbackCoilBlock, self).getValues(address, count=count)

    def setValues(self, address, values):
        i = 0
        for mb_adr in range(address, (address + len(values))):

            try:
                if (mb_adr == 1001):
                    b.set_group(5,'on',values[i])

                elif (mb_adr == 1010): # All lamps Off
                    b.set_group(0,'on',values[i])
                else:
                    hue_adr = mb_adr - 1
                    if (hue_adr < nofLamps):
                        lights[hue_adr].on = values[i]

            except KeyError:
                pass

            i += 1
        super(CallbackCoilBlock, self).setValues(address, values)

class CallbackDigitalInputBlock(ModbusSparseDataBlock):
    """ A datablock that stores the new value in memory
    and passes the operation to a message queue for further
    processing.
    """

    def __init__(self):

        values = {i:False for i in range(0, 2000)}
        super(CallbackDigitalInputBlock, self).__init__(values)

    def getValues(self, address, count=1):
        values = []
        for mb_adr in range(address, (address + count)):
            hue_adr = mb_adr - 1

            if (hue_adr < nofLamps):
                value = bool(lights[hue_adr].reachable)
            else:
                value = False

            values.extend([value])

        super(CallbackDigitalInputBlock, self).setValues(address, values)
        return super(CallbackDigitalInputBlock, self).getValues(address, count=count)

class CallbackInputBlock(ModbusSparseDataBlock):
    """ A datablock that stores the new value in memory
    and passes the operation to a message queue for further
    processing.
    """

    def __init__(self):
        values = {i:int("0xFFFF",0) for i in range(0, 2000)}
        values[0xbeef] = len(values)  # the number of devices
        super(CallbackInputBlock, self).__init__(values)

    def getValues(self, address, count=1):
        values = []
        for mb_adr in range(address , (address + count)):
            value = int("0xFFFF",0) # Default value [-1] until read from hue

            try:

                # Special functions down here
                if (mb_adr == 1001):
                    value = b.get_group(5)['action']['bri']
                elif (mb_adr == 1101):
                    value = b.get_group(5)['action']['hue']
                elif (mb_adr == 1201):
                    value = b.get_group(5)['action']['sat']

                else: # Modbus addresses for light functions

                    hue_adr = mb_adr - 1 if mb_adr <= 100 else mb_adr - 101 if mb_adr <= 200 else mb_adr - 201 if mb_adr <= 300 else -1

                    if (hue_adr == -1 or hue_adr >= nofLamps):
                        values.extend([int(value)])
                        continue
            
                    if(mb_adr <= 100):
                        value = lights[hue_adr].brightness
                    elif(mb_adr <= 200):
                        value = lights[hue_adr].hue
                    elif(mb_adr <= 300):
                        value = lights[hue_adr].saturation

            except KeyError:
                pass

            values.extend([int(value)])

        super(CallbackInputBlock, self).setValues(address, values)
        return super(CallbackInputBlock, self).getValues(address, count=count)

class CallbackRegisterBlock(ModbusSparseDataBlock):
    """ A datablock that stores the new value in memory
    and passes the operation to a message queue for further
    processing.
    """

    def __init__(self):
        values = {i:int("0xFFFF",0) for i in range(0, 2000)}  
        super(CallbackRegisterBlock, self).__init__(values)

    def getValues(self, address, count=1):
        values = []
        for mb_adr in range(address , (address + count)):
            value = int("0xFFFF",0) # Default value [-1] until read from hue

            try:
                
                # Special functions
                if (mb_adr == 1001):
                    value = b.get_group(5)['action']['bri']
                elif (mb_adr == 1101):
                    value = b.get_group(5)['action']['hue']
                elif (mb_adr == 1201):
                    value = b.get_group(5)['action']['sat']
                else: # Modbus addresses for light functions

                    hue_adr = mb_adr - 1 if mb_adr <= 100 else mb_adr - 101 if mb_adr <= 200 else mb_adr - 201 if mb_adr <= 300 else -1

                    if (hue_adr == -1 or hue_adr >= nofLamps):
                        values.extend([int(value)])
                        continue
            
                    if(mb_adr <= 100):
                        value = lights[hue_adr].brightness
                    elif(mb_adr <= 200):
                        value = lights[hue_adr].hue
                    elif(mb_adr <= 300):
                        value = lights[hue_adr].saturation

            except KeyError:
                pass

            values.extend([int(value)])

        super(CallbackRegisterBlock, self).setValues(address, values)
        return super(CallbackRegisterBlock, self).getValues(address, count=count)

    def setValues(self, address, values):
        i = 0
        for mb_adr in range(address, (address + len(values))):
            
            try:
                if (mb_adr == 1001):
                    b.set_group(5,'bri',values[i])
                elif (mb_adr == 1101):
                    b.set_group(5,'hue',values[i])
                elif (mb_adr == 1201):
                    b.set_group(5,'sat',values[i])
                else:

                    hue_adr = mb_adr - 1 if mb_adr <= 100 else mb_adr - 101 if mb_adr <= 200 else mb_adr - 201 if mb_adr <= 300 else -1
                    if (hue_adr == -1 or hue_adr >= nofLamps):

                        i += 1
                        continue

                    if(mb_adr <= 100):
                        lights[hue_adr].brightness = values[i] if (values[i] <= 254) else 254  # Max value
                    elif(mb_adr <= 200):
                        lights[hue_adr].hue = values[i] if (values[i] <= 65535) else 65535   # Max value
                    elif(mb_adr <= 300):
                        lights[hue_adr].saturation = values[i] if (values[i] <= 254) else 254  # Max value

            except KeyError:
                pass
            i += 1

        super(CallbackRegisterBlock, self).setValues(address, values)


def run_updating_server():

    block_di = CallbackDigitalInputBlock()
    block_co = CallbackCoilBlock()
    block_reg = CallbackRegisterBlock()
    block_ipt = CallbackInputBlock()

    store = ModbusSlaveContext(di = block_di, co = block_co, hr = block_reg, ir = block_ipt)
    context = ModbusServerContext(slaves=store, single=True)

    #---------------------------------------------------------------------------#
    # initialize the server information
    #---------------------------------------------------------------------------#
    # If you don't set this or any fields, they are defaulted to empty strings.
    #---------------------------------------------------------------------------#
    identity = ModbusDeviceIdentification()
    identity.VendorName  = 'Pymodbus'
    identity.ProductCode = 'PM'
    identity.VendorUrl   = 'http://github.com/bashwork/pymodbus/'
    identity.ProductName = 'Pymodbus Server'
    identity.ModelName   = 'Pymodbus Server'
    identity.MajorMinorRevision = '1.0'


    #---------------------------------------------------------------------------#
    # run the server you want
    #---------------------------------------------------------------------------#

    StartTcpServer(context, identity=identity, address=("localhost", 502))

if __name__ == "__main__":
    run_updating_server()