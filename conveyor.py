# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 15:13:39 2020

@author: sbachchuwar
"""
import sys
import random
import logging
'''
Assumptions:
    - Each Pair of Worker are divided in Left side worker & Right side worker. Left side worker have higher priority of using 
    belt than right side worker. That means, for each new cycle left side worker will act on Belt first. If he performs action 
    on Belt, Right side worker does nothing but if Left side worker do not perform any action on belt, Right side worker will 
    perform action on Belt.
    - Results will have count of products which came off production line and not which are built but still on the belt.
    - Results will have count of components which came off production line without being picked and not which are still on Belt
    
Please set logging level to DEBUG if step by step logs are required
'''
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
#logging.basicConfig(level=logging.INFO, stream=sys.stdout)

class Worker():
    def __init__(self, belt, name):
        '''
        Worker class maintains properties of Worker & Operations to be performed by Workers.
        '''
        self.items_in_hand = []
        self.busy = 0 # 0 means ready to use belt, 1 or higher value indicates worker is busy.
        self.belt = belt
        self.name = name
    
    def execute(self, item, slot):
        '''
        Worker.execute() accepts slot number & component available on that slot to perform worker's operation to assemble the 
        product. 
        
        Only one worker can perform action on Belt in one cycle.:
        return 1, if worker didn't perform any action on Belt, ask opposite worker to act.
        return 0, if worker performed action on Belt, end the cycle.
        
        '''
        logging.debug("Operating Worker: {}".format(self.name))
        #Check if Worker in assembly state or ready to use belt to pick or drop item
        if self.busy > 1:
            logging.debug("{} is in assembly state, waiting cycle :{}".format(self.name, self.busy))
            self.busy -= 1
            return 1
        elif self.busy == 1:
            #Last waiting assembly cycle: Prepare items in hand to perform action on belt in next cycle.
            logging.debug("{} is ready to pick new component & put a product, waiting cycle :{}".format(self.name, self.busy))
            self.items_in_hand.clear()
            self.items_in_hand.append('P')
            logging.debug("Added product, check items in hand:{}".format(self.items_in_hand))
            self.busy -= 1
            return 1  # return 1 when worker didn't act on Belt
        #if worker is ready to perform action on belt
        else:
            if item == '': 
                #If slot found empty & product is ready, drop P on Belt.
                if self.belt.product in self.items_in_hand: 
                    self.belt.updateBelt(self.belt.product, slot)
                    logging.debug("{}:Current items in hand:{}".format(self.name, self.items_in_hand))
                    logging.debug("{}:Kept Product on Belt".format(self.name))
                    self.items_in_hand.remove(self.belt.product)
                    return 0  # return 0 when worker acted on Belt
                else:
                    return 1
                    
            else: # If Slot has either A or B
                if item in self.items_in_hand or len(self.items_in_hand) == len(self.belt.components):
                    logging.debug("{}: Ignoring, Reason-Already got this component or Hands are full ".format(self.name))
                    return 1
                else:
                    logging.debug("{}:Found missing component".format(self.name))
                    self.items_in_hand.append(item)
                    self.belt.updateBelt('', slot)
                if all( i in self.items_in_hand for i in self.belt.components):
                    logging.debug("{}:all components in hand, going to (busy)assembly state".format(self.name))
                    self.busy = self.belt.assembly_time  # Going in assembly state, will need 3 cycles to prepare product.
                return 0
        
class Belt():
    '''Defines properties of belt with components under production & expected outcome on Belt'''
    def __init__(self, slots, comp, prod):
        self.slots = slots
        self.components = comp
        self.product = prod
        self.source_items = self.components.copy()
        self.source_items.append('')
        self.items_on_belt = ['']*slots
        self.assembly_time = 3
        
    def updateBelt(self, item, index):
        '''updates item on specific slot on Belt'''
        self.items_on_belt[index] = item
            #Productivity(Belt).counter(self.items_on_belt.pop())
    
    def getBeltStatus(self):
        '''Returns current item list on Belt'''
        return self.items_on_belt
        
class Productivity():
    '''
    Productivity class manages counting items going off the production line & report Productivity status.
    '''
    def __init__(self, belt):
        self.waste_count = 0
        self.prod_count = 0
        self.belt = belt
        
    def counter(self, dropped_item):
        '''Counts items going off the production line'''
        if not dropped_item == '':
            if dropped_item == self.belt.product:
                logging.debug('Product dropped'+20*'-')
                self.prod_count += 1
            else:
                self.waste_count += 1
                logging.debug("Component dropped"+20*'-')
            
    def getProductStatus(self):
        '''Provide the production status'''
        logging.info("Number of Products came off the production line: {}".format(self.prod_count))
        logging.info("Number of Components went off the belt without interaction: {}".format(self.waste_count))
            
class Factory():
    '''
    Factory class will start the conveyor belt for mentioned cycle.
    This will take care of generating random components on belt & calling workers to perform 
    action on items on belt
    '''
    def __init__(self, total_cycles, belt_obj):
        self.belt = belt_obj
        self.total_cycles = total_cycles
        self.slots = self.belt.slots
        self.worker_count = self.belt.slots * 2
        self.items_on_belt = self.belt.getBeltStatus()
        self.l_worker = dict()
        self.r_worker = dict()
        self.temp = 0
        self.next_item = ''
        self.prod = Productivity(self.belt)
    
    def getNextItem(self):
        '''
        Random component generator with 1/3 chance of containing empty slot.
        '''
        random_item = random.choice(self.belt.source_items)  # Get next random item
        logging.debug("Random Item:{}".format(random_item))
        if random_item == '':
            self.temp = 0
        else:
            if self.temp < 2:
                self.temp += 1
            else:
                logging.debug("Empty slot is expected in 1 out of 3 cycles, discarding generated random item & keeping slot empty.")
                random_item = ''            
        return random_item
        
    
    def start(self):
        '''
        Factory.start() function will put random components at start of slot with throwing last component 
        off the production line. For every cycle, each item on Conveyor belt will be sent to Worker class 
        to perform required operation
        
        Assumption: Considering Left side Worker has higher priority than right side workers.
        
        If left side worker doesn't perform any action on belt, right side worker will get chance to 
        perform operation.  
        '''
        for i in range(self.slots):
            self.l_worker[i] = Worker(self.belt, "%s%s"%('l_worker', i))
            self.r_worker[i] = Worker(self.belt, "%s%s"%('r_worker', i))
        self.temp = 0
        for cycle in range(self.total_cycles):
            logging.debug("Running cycle {}".format(cycle))
            self.next_item = self.getNextItem()
            # Push random item on Belt & pop last item.
            self.belt.items_on_belt.insert(0, self.next_item) 
            dropped_item = self.belt.items_on_belt.pop()
            self.prod.counter(dropped_item)
            items_on_belt = self.belt.items_on_belt
            logging.debug("Belt:{}".format(items_on_belt))
            #call workers with each item on Belt 
            for slot, item in enumerate(items_on_belt):
                logging.debug("slot:{}, item:{}".format(slot, item))
                if not item == self.belt.product:
                    if self.l_worker[slot].execute(item, slot) == 1:  # If l_worker return 1 means r_worker get a chance
                        self.r_worker[slot].execute(item, slot)
        self.prod.getProductStatus()

if __name__ == "__main__":
    '''
    steps: Number of cycles.
    slots: Length of the belt. Considering 3 here, as we have 3 pairs of workers where 1 pair operating on single belt.
    components: Raw Material
    Product: Final Product
    '''
    steps = 100
    slots = 3
    components = ['A','B']
    product = 'P'
    belt = Belt(slots, components, product)
    factory = Factory(steps, belt)
    factory.start()
